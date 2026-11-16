import os
import json
import time
import shutil
import socket
import tempfile
import threading
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import httpx


def pick_folder_dialog(title: str = "Seleccionar carpeta — TidyDesk AI") -> Optional[str]:
    """Abre el diálogo nativo de selección de carpetas de Windows siempre al frente (TopMost)."""
    selected_path: Optional[str] = None

    def _run_tk():
        nonlocal selected_path
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()

            folder = filedialog.askdirectory(
                parent=root,
                title=title,
                mustexist=True,
            )
            root.destroy()
            if folder:
                # Normalizar a barras invertidas nativas de Windows
                selected_path = str(Path(folder).resolve())
        except Exception:
            selected_path = None

    # Ejecutar en hilo dedicado para evitar conflictos con el event loop de asyncio
    t = threading.Thread(target=_run_tk)
    t.start()
    t.join(timeout=120.0)
    return selected_path


def find_ollama_executable() -> Optional[Path]:
    """Busca el ejecutable de Ollama en el PATH o en las rutas estándar de Windows."""
    which_path = shutil.which("ollama")
    if which_path:
        return Path(which_path)

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")

    candidates = [
        Path(local_app_data) / "Programs" / "Ollama" / "ollama.exe",
        Path(program_files) / "Ollama" / "ollama.exe",
        Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def is_ollama_port_open() -> bool:
    """Verifica en <100ms si Ollama está escuchando en 127.0.0.1:11434."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.15)
        return s.connect_ex(("127.0.0.1", 11434)) == 0


def ensure_ollama_running_if_installed() -> None:
    """Si Ollama está instalado en la PC pero apagado, lo levanta silenciosamente en segundo plano."""
    if is_ollama_port_open():
        return
    exe_path = find_ollama_executable()
    if exe_path:
        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            subprocess.Popen(
                [str(exe_path), "serve"],
                creationflags=creation_flags,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass


class OllamaSetupManager:
    """Gestiona la detección, auto-instalación de Ollama y descarga de modelos con progreso en vivo."""

    def __init__(self):
        self.state: str = "idle"  # idle | downloading_installer | installing | starting_service | pulling_model | ready | error
        self.progress: int = 0
        self.message: str = ""
        self.target_model: str = "llama3.2:1b"
        self._lock = threading.Lock()
        self._working = False

    def get_status(self) -> Dict[str, Any]:
        exe_path = find_ollama_executable()
        installed = exe_path is not None
        running = is_ollama_port_open()

        # Espacio libre en disco del sistema
        try:
            usage = shutil.disk_usage(Path.home().anchor or "C:\\")
            free_gb = round(usage.free / (1024 ** 3), 1)
        except Exception:
            free_gb = 0.0

        models = []
        if running:
            try:
                with httpx.Client(timeout=1.5) as client:
                    res = client.get("http://127.0.0.1:11434/api/tags")
                    if res.status_code == 200:
                        models = [m.get("name") for m in res.json().get("models", [])]
            except Exception:
                pass

        return {
            "installed": installed,
            "executable_path": str(exe_path) if exe_path else None,
            "running": running,
            "models": models,
            "free_disk_gb": free_gb,
            "setup_state": self.state,
            "setup_progress": self.progress,
            "setup_message": self.message,
            "is_working": self._working,
        }

    def start_auto_setup(self, model_name: str = "llama3.2:1b") -> Dict[str, Any]:
        with self._lock:
            if self._working:
                return self.get_status()
            self._working = True
            self.target_model = model_name or "llama3.2:1b"
            self.state = "starting"
            self.progress = 2
            self.message = "Verificando instalación de Ollama en el sistema..."

        worker = threading.Thread(target=self._run_setup_pipeline, daemon=True)
        worker.start()
        return self.get_status()

    def _run_setup_pipeline(self):
        try:
            exe_path = find_ollama_executable()

            # PASO 1: Si no está instalado, descargar e instalar OllamaSetup.exe
            if not exe_path:
                self.state = "downloading_installer"
                self.progress = 5
                self.message = "Descargando instalador oficial de Ollama (OllamaSetup.exe)..."

                installer_path = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
                url = "https://ollama.com/download/OllamaSetup.exe"

                with httpx.Client(follow_redirects=True, timeout=60.0) as client:
                    with client.stream("GET", url) as r:
                        r.raise_for_status()
                        total = int(r.headers.get("Content-Length", 0))
                        downloaded = 0
                        with open(installer_path, "wb") as f:
                            for chunk in r.iter_bytes(chunk_size=65536):
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total > 0:
                                    pct = int((downloaded / total) * 40)
                                    self.progress = 5 + pct
                                    mb_done = downloaded / (1024 * 1024)
                                    mb_total = total / (1024 * 1024)
                                    self.message = f"Descargando OllamaSetup.exe ({mb_done:.1f} MB / {mb_total:.1f} MB)..."

                self.state = "installing"
                self.progress = 48
                self.message = "Instalando Ollama en Windows (puede tardar 1 minuto)..."

                # Ejecutar instalador en modo silencioso
                subprocess.run([str(installer_path), "/SILENT"], check=False)

                # Verificar si apareció el binario
                for _ in range(30):
                    exe_path = find_ollama_executable()
                    if exe_path:
                        break
                    time.sleep(1.0)

                if not exe_path:
                    raise RuntimeError("No se detectó el binario de Ollama tras la instalación.")

            # PASO 2: Iniciar el servicio si no está corriendo
            if not is_ollama_port_open():
                self.state = "starting_service"
                self.progress = 55
                self.message = "Iniciando servidor local de Ollama en segundo plano..."

                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.Popen(
                    [str(exe_path), "serve"],
                    creationflags=creation_flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                for _ in range(25):
                    if is_ollama_port_open():
                        break
                    time.sleep(0.5)

            if not is_ollama_port_open():
                raise RuntimeError("El servicio de Ollama no respondió en el puerto 11434.")

            # PASO 3: Descargar (pull) el modelo ligero seleccionado
            self.state = "pulling_model"
            self.progress = 60
            self.message = f"Descargando modelo de IA '{self.target_model}'..."

            with httpx.Client(timeout=600.0) as client:
                with client.stream(
                    "POST",
                    "http://127.0.0.1:11434/api/pull",
                    json={"name": self.target_model, "stream": True},
                ) as r:
                    r.raise_for_status()
                    for line in r.iter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            status_txt = data.get("status", "Descargando...")
                            total = data.get("total", 0)
                            completed = data.get("completed", 0)
                            if total > 0:
                                ratio = completed / total
                                self.progress = 60 + int(ratio * 39)
                                mb_c = completed / (1024 * 1024)
                                mb_t = total / (1024 * 1024)
                                self.message = f"Descargando {self.target_model}: {mb_c:.0f} MB / {mb_t:.0f} MB ({ int(ratio * 100) }%)"
                            else:
                                self.message = f"Modelo {self.target_model}: {status_txt}"
                        except Exception:
                            pass

            self.state = "ready"
            self.progress = 100
            self.message = f"¡Ollama y el modelo '{self.target_model}' están instalados y listos para usar!"

        except Exception as e:
            self.state = "error"
            self.message = f"Inconveniente durante la instalación: {str(e)}"
        finally:
            with self._lock:
                self._working = False


ollama_setup_manager = OllamaSetupManager()
