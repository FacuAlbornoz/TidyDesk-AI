import os
import sys
import time
import ctypes
import shutil
import socket
import threading
import subprocess
import webbrowser
from pathlib import Path
from PIL import Image
import pystray
import uvicorn

# Registrar AppUserModelID en Windows 10/11 para barra de tareas y notificaciones
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FacuAlbornoz.TidyDeskAI.ProStudio.2.2")
except Exception:
    pass

# Asegurar que el directorio backend esté en sys.path
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# En modo sin consola (pythonw.exe o PyInstaller --noconsole), stdout/stderr son None
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

from app.main import app
from app.config import DESKTOP_DIR, DOWNLOADS_DIR, DATA_DIR
from app.core.guardian import guardian_manager, send_windows_toast
from app.core.system_utils import create_pro_brand_icon

APP_URL = "http://127.0.0.1:8000"
PORT = 8000


def is_port_in_use(port: int = PORT) -> bool:
    """Comprueba si el servidor ya está corriendo en el puerto local."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def open_native_app_window(url: str = APP_URL) -> None:
    """Abre TidyDesk AI como ventana de aplicación de escritorio nativa con su propio perfil de icono."""
    profile_dir = DATA_DIR / "window_profile"
    try:
        profile_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    candidates = [
        shutil.which("msedge"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        shutil.which("chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("brave"),
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    ]
    for bin_path in candidates:
        if bin_path and os.path.exists(bin_path):
            try:
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.Popen(
                    [
                        bin_path,
                        f"--app={url}",
                        "--window-size=1340,860",
                        f"--user-data-dir={profile_dir}",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                    creationflags=creation_flags,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except Exception:
                continue

    webbrowser.open(url)


def create_tray_icon_image(guardian_active: bool = False) -> Image.Image:
    """Genera el icono oficial HD de TidyDesk AI para la bandeja del sistema."""
    return create_pro_brand_icon(size=128, guardian_active=guardian_active)


class TidyDeskTrayApp:
    """Controlador nativo de Bandeja del Sistema (System Tray) para Windows."""

    def __init__(self, open_browser_on_start: bool = True):
        self.open_browser_on_start = open_browser_on_start
        self.server: uvicorn.Server | None = None
        self.server_thread: threading.Thread | None = None
        self.icon: pystray.Icon | None = None

    def start_backend_server(self):
        """Inicia FastAPI/Uvicorn en un hilo demonio silencioso."""
        if is_port_in_use(PORT):
            return

        config = uvicorn.Config(
            app=app,
            host="127.0.0.1",
            port=PORT,
            log_level="warning",
            access_log=False,
        )
        self.server = uvicorn.Server(config)
        self.server_thread = threading.Thread(target=self.server.run, daemon=True)
        self.server_thread.start()

        # Esperar hasta que el servidor esté listo (máx 4s)
        for _ in range(40):
            if is_port_in_use(PORT):
                break
            time.sleep(0.1)

    def on_open_dashboard(self, icon=None, item=None):
        """Abre la interfaz en una ventana de aplicación nativa de escritorio."""
        open_native_app_window(APP_URL)

    def on_toggle_guardian(self, icon, item):
        """Activa o pausa el Modo Guardián directamente desde el System Tray."""
        if guardian_manager.is_running:
            guardian_manager.stop()
            send_windows_toast("TidyDesk AI", "Modo Guardián pausado.")
        else:
            guardian_manager.start()
            send_windows_toast(
                "🛡️ TidyDesk AI — Guardián Activo",
                f"Vigilando en tiempo real: {guardian_manager.watched_path.name}",
            )
        self.refresh_icon()

    def on_open_downloads(self, icon=None, item=None):
        if DOWNLOADS_DIR.exists():
            os.startfile(str(DOWNLOADS_DIR))

    def on_open_desktop(self, icon=None, item=None):
        if DESKTOP_DIR.exists():
            os.startfile(str(DESKTOP_DIR))

    def on_exit(self, icon=None, item=None):
        """Detiene el Guardián, apaga el servidor Uvicorn y cierra el icono de bandeja."""
        guardian_manager.stop()
        if self.server is not None:
            self.server.should_exit = True
        if self.icon is not None:
            self.icon.stop()

    def refresh_icon(self):
        """Actualiza el color del icono y el título según el estado del Guardián."""
        if self.icon is not None:
            active = guardian_manager.is_running
            self.icon.icon = create_tray_icon_image(guardian_active=active)
            status_str = "🛡️ Guardián Activo" if active else "En espera"
            self.icon.title = f"TidyDesk AI v2.0 — {status_str}"

    def build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                "🗂️ Abrir Panel TidyDesk AI",
                self.on_open_dashboard,
                default=True,
            ),
            pystray.MenuItem(
                "🛡️ Modo Guardián (Tiempo Real)",
                self.on_toggle_guardian,
                checked=lambda item: guardian_manager.is_running,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("📥 Abrir Carpeta Descargas", self.on_open_downloads),
            pystray.MenuItem("🖥️ Abrir Carpeta Escritorio", self.on_open_desktop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Salir de TidyDesk AI", self.on_exit),
        )

    def run(self):
        if is_port_in_use(PORT):
            # Si ya hay una instancia corriendo en segundo plano, simplemente abrir la ventana nativa
            open_native_app_window(APP_URL)
            return

        self.start_backend_server()

        if self.open_browser_on_start:
            open_native_app_window(APP_URL)

        send_windows_toast(
            "🗂️ TidyDesk AI v2.1 Iniciado",
            "Ejecutándose como App Nativa y en la bandeja del sistema.",
        )

        self.icon = pystray.Icon(
            name="TidyDeskAI",
            icon=create_tray_icon_image(guardian_active=guardian_manager.is_running),
            title="TidyDesk AI v2.1 — Organizador Inteligente",
            menu=self.build_menu(),
        )
        self.icon.run()


if __name__ == "__main__":
    no_browser = "--minimized" in sys.argv
    tray = TidyDeskTrayApp(open_browser_on_start=not no_browser)
    tray.run()
