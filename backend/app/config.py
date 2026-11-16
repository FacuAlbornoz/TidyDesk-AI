from pathlib import Path
import os

# Rutas del Proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"
RULES_FILE = DATA_DIR / "rules.json"
FRONTEND_DIR = BASE_DIR / "frontend"

# Crear directorio de datos si no existe
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

# Rutas estándar del usuario en Windows
USER_PROFILE = Path(os.environ.get("USERPROFILE", Path.home()))
DESKTOP_DIR = USER_PROFILE / "Desktop"
DOWNLOADS_DIR = USER_PROFILE / "Downloads"

# Extensiones protegidas (JAMÁS tocar ni mover)
BLACKLIST_EXTENSIONS = {
    ".lnk",    # Accesos directos de Windows
    ".url",    # Accesos directos de Internet
    ".ini",    # Configuraciones de escritorio (desktop.ini)
    ".sys",    # Archivos de sistema
    ".bat",    # Scripts de procesamiento por lotes del sistema
    ".cmd",    # Scripts de comando
    ".vbs",    # Scripts Visual Basic
    ".dll",    # Librerías dinámicas
}

# Nombres de archivos y carpetas protegidos
BLACKLIST_FILENAMES = {
    "desktop.ini",
    "thumbs.db",
    "ntuser.dat",
    ".ds_store",
    ".git",
    ".gitignore",
}

# Configuración de IA
DEFAULT_OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
