import time
import uuid
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.config import BLACKLIST_FILENAMES, BLACKLIST_EXTENSIONS
from app.core.scanner import resolve_target_folder, is_safe_to_organize
from app.core.rules_manager import match_custom_rule
from app.core.organizer import execute_plan
from app.core.history import load_history
from app.core.multimodal import (
    GENERIC_PDF_PATTERNS,
    GENERIC_IMAGE_PATTERNS,
    is_generic_filename,
    extract_pdf_text,
    heuristic_rename_pdf,
    heuristic_rename_image,
)
from app.ai.rules_provider import SmartRulesProvider
from app.schemas.organize import PlanItem
from app.schemas.guardian import GuardianConfig, GuardianEvent, GuardianStatusResponse

# Extensiones temporales de navegadores en curso de descarga
TEMP_DOWNLOAD_EXTENSIONS = {
    ".crdownload",
    ".part",
    ".tmp",
    ".download",
    ".opdownload",
    ".partial",
}


def send_windows_toast(title: str, message: str) -> None:
    """Envía una notificación nativa en Windows de forma asíncrona y no bloqueante."""
    ps_script = f"""
    [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
    $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
    $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
    $objNotifyIcon.BalloonTipIcon = "Info"
    $objNotifyIcon.BalloonTipText = "{message.replace('"', "'")}"
    $objNotifyIcon.BalloonTipTitle = "{title.replace('"', "'")}"
    $objNotifyIcon.Visible = $True
    $objNotifyIcon.ShowBalloonTip(4000)
    Start-Sleep -Seconds 4
    $objNotifyIcon.Dispose()
    """
    try:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_script],
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


class _GuardianHandler(FileSystemEventHandler):
    """Manejador de eventos de sistema de archivos para watchdog."""

    def __init__(self, manager: "GuardianManager"):
        super().__init__()
        self.manager = manager

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self.manager.schedule_file_processing(Path(event.src_path))

    def on_moved(self, event: FileSystemEvent):
        # Los navegadores descargan como .crdownload y al finalizar renombran al archivo final
        if not event.is_directory and hasattr(event, "dest_path"):
            dest = Path(event.dest_path)
            # Solo procesar si se movió dentro de la raíz vigilada
            if dest.parent.resolve() == self.manager.watched_path.resolve():
                self.manager.schedule_file_processing(dest)


class GuardianManager:
    """Servicio singleton que gestiona el demonio Watchdog en segundo plano."""

    def __init__(self):
        self.config = GuardianConfig(
            enabled=False,
            folder_type="downloads",
            mode="all",
            enable_smart_rename=True,
            windows_notifications=True,
        )
        self._observer: Observer | None = None
        self._lock = threading.Lock()
        self._processing_paths: Set[str] = set()
        self.events: List[GuardianEvent] = []
        self.total_processed_session: int = 0
        self.rules_classifier = SmartRulesProvider()

    @property
    def watched_path(self) -> Path:
        try:
            return resolve_target_folder(self.config.folder_type, self.config.custom_path)
        except Exception:
            return resolve_target_folder("downloads")

    @property
    def is_running(self) -> bool:
        return self._observer is not None and self._observer.is_alive()

    def start(self, new_config: GuardianConfig | None = None) -> GuardianStatusResponse:
        with self._lock:
            if new_config is not None:
                self.config = new_config
            self.config.enabled = True

            self._stop_internal()

            target = self.watched_path
            if not target.exists():
                self.config.enabled = False
                return self.get_status()

            handler = _GuardianHandler(self)
            self._observer = Observer()
            self._observer.schedule(handler, str(target), recursive=False)
            self._observer.daemon = True
            self._observer.start()

        return self.get_status()

    def stop(self) -> GuardianStatusResponse:
        with self._lock:
            self.config.enabled = False
            self._stop_internal()
        return self.get_status()

    def _stop_internal(self):
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=2.0)
            except Exception:
                pass
            finally:
                self._observer = None

    def clear_events(self) -> GuardianStatusResponse:
        with self._lock:
            self.events.clear()
        return self.get_status()

    def get_status(self) -> GuardianStatusResponse:
        # Sincronizar estado 'reverted' con el historial global
        history_map = {tx.get("transaction_id"): tx.get("reverted", False) for tx in load_history()}
        for ev in self.events:
            if ev.transaction_id in history_map:
                ev.reverted = history_map[ev.transaction_id]

        return GuardianStatusResponse(
            running=self.is_running,
            watched_path=str(self.watched_path),
            config=self.config,
            events=list(self.events),
            total_processed_session=self.total_processed_session,
        )

    def schedule_file_processing(self, file_path: Path):
        """Lanza un hilo ligero para aguardar a que la descarga termine y organizar el archivo."""
        norm_path = str(file_path.resolve())

        # Filtros rápidos inmediatos
        if file_path.name.lower() in BLACKLIST_FILENAMES:
            return
        if file_path.name.startswith("~$") or file_path.name.startswith("."):
            return
        ext = file_path.suffix.lower()
        if ext in TEMP_DOWNLOAD_EXTENSIONS or ext in BLACKLIST_EXTENSIONS:
            return

        with self._lock:
            if norm_path in self._processing_paths:
                return
            self._processing_paths.add(norm_path)

        worker = threading.Thread(
            target=self._process_file_when_ready,
            args=(file_path, norm_path),
            daemon=True,
        )
        worker.start()

    def _wait_until_file_ready(self, file_path: Path, timeout: float = 15.0, settle_time: float = 0.6) -> bool:
        """Espera hasta que el archivo deje de crecer y no esté bloqueado por el navegador o antivirus."""
        start_time = time.time()
        last_size = -1

        while (time.time() - start_time) < timeout:
            if not file_path.exists():
                return False

            try:
                current_size = file_path.stat().st_size
                if current_size > 0 and current_size == last_size:
                    # Comprobar que no tiene bloqueo exclusivo de escritura
                    with open(file_path, "rb"):
                        return True
                last_size = current_size
            except (PermissionError, OSError):
                pass

            time.sleep(settle_time)

        return False

    def _process_file_when_ready(self, file_path: Path, norm_path: str):
        try:
            if not self._wait_until_file_ready(file_path):
                return

            safe, _ = is_safe_to_organize(file_path, include_shortcuts=False)
            if not file_path.exists() or not safe:
                return

            # Asegurar que el archivo sigue estando directamente en la carpeta vigilada
            if file_path.parent.resolve() != self.watched_path.resolve():
                return

            orig_name = file_path.name
            ext = file_path.suffix.lower()

            # 1. Evaluar Reglas Personalizadas primero
            custom_match = match_custom_rule(orig_name, ext)
            if custom_match:
                suggested_folder, reason = custom_match
            else:
                if self.config.mode == "custom_only":
                    # En modo solo reglas personalizadas, ignorar el resto
                    return
                suggested_folder, reason = self.rules_classifier._classify_file(orig_name, ext)

            # 2. Evaluar Renombrado Multimodal si está activo
            suggested_name = orig_name
            if self.config.enable_smart_rename:
                if ext == ".pdf" and (is_generic_filename(orig_name, GENERIC_PDF_PATTERNS) or len(file_path.stem) < 8):
                    text = extract_pdf_text(file_path)
                    new_name = heuristic_rename_pdf(orig_name, text)
                    if new_name and new_name.lower() != orig_name.lower():
                        suggested_name = new_name
                        reason += " | ✨ Renombrado por Guardián"
                elif ext in [".png", ".jpg", ".jpeg", ".webp"] and is_generic_filename(orig_name, GENERIC_IMAGE_PATTERNS):
                    new_name = heuristic_rename_image(orig_name, file_path)
                    if new_name and new_name.lower() != orig_name.lower():
                        suggested_name = new_name
                        reason += " | ✨ Renombrado por Guardián"

            # 3. Ejecutar movimiento atómico con registro en Historial para Rollback
            plan_item = PlanItem(
                file_id=f"guard_{uuid.uuid4().hex[:8]}",
                original_path=str(file_path.resolve()),
                original_name=orig_name,
                suggested_folder=suggested_folder,
                suggested_name=suggested_name,
                reason=f"🛡️ Guardián: {reason}",
                selected=True,
            )

            exec_res = execute_plan(self.watched_path, [plan_item])
            if exec_res.success and exec_res.moved_count > 0:
                ev = GuardianEvent(
                    event_id=f"ev_{uuid.uuid4().hex[:8]}",
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                    original_name=orig_name,
                    new_name=suggested_name,
                    destination_folder=suggested_folder,
                    reason=reason,
                    transaction_id=exec_res.transaction_id,
                    reverted=False,
                )
                with self._lock:
                    self.events.insert(0, ev)
                    if len(self.events) > 50:
                        self.events = self.events[:50]
                    self.total_processed_session += 1

                if self.config.windows_notifications:
                    send_windows_toast(
                        "🛡️ TidyDesk AI — Archivo Organizado",
                        f"{orig_name} → {suggested_folder}"
                    )
        except Exception:
            pass
        finally:
            with self._lock:
                self._processing_paths.discard(norm_path)


# Instancia global del Guardián
guardian_manager = GuardianManager()
