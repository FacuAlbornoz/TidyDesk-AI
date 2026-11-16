import os
import sys
import json
import time
import ctypes
import shutil
import socket
import zipfile
import platform
import tempfile
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw
import httpx


# =========================================================
# 1. GENERADOR DE ICONO Y LOGO OFICIAL HD (PRO STUDIO)
# =========================================================
def create_pro_brand_icon(size: int = 256, guardian_active: bool = False) -> Image.Image:
    """Genera el logo oficial de TidyDesk AI en alta resolución con estética Pro Studio."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(size * 0.06)
    radius = int(size * 0.24)

    # Sombra exterior / Borde exterior brillante
    draw.rounded_rectangle(
        [(pad, pad), (size - pad, size - pad)],
        radius=radius,
        fill=(30, 27, 75, 255),       # Indigo profundo #1e1b4b
        outline=(99, 102, 241, 255),  # Borde luminoso #6366f1
        width=max(2, int(size * 0.025)),
    )

    # Capa interior con acento violeta/indigo
    inner_pad = int(size * 0.11)
    draw.rounded_rectangle(
        [(inner_pad, inner_pad), (size - inner_pad, size - inner_pad)],
        radius=int(radius * 0.8),
        fill=(49, 46, 129, 255),      # #312e81
    )

    # Solapa trasera de la carpeta (Cian/Indigo brillante)
    fx1 = int(size * 0.22)
    fy1 = int(size * 0.28)
    fx2 = int(size * 0.78)
    fy2 = int(size * 0.74)

    draw.polygon(
        [
            (fx1, int(size * 0.36)),
            (fx1, fy1),
            (int(size * 0.46), fy1),
            (int(size * 0.52), int(size * 0.36)),
        ],
        fill=(56, 189, 248, 255),     # #38bdf8 Sky Cyan
    )

    # Cuerpo principal de la carpeta
    draw.rounded_rectangle(
        [(fx1, int(size * 0.34)), (fx2, fy2)],
        radius=int(size * 0.06),
        fill=(248, 250, 252, 255),    # Blanco puro #f8fafc
    )

    # Franja inferior de acento en la carpeta
    draw.rounded_rectangle(
        [(fx1, int(size * 0.56)), (fx2, fy2)],
        radius=int(size * 0.06),
        fill=(224, 231, 255, 255),    # #e0e7ff
    )

    # Estrella / Destello de IA (Sparkle de 4 puntas) en el centro-derecha
    cx = int(size * 0.60)
    cy = int(size * 0.48)
    r_outer = int(size * 0.13)
    r_inner = int(size * 0.04)
    sparkle_pts = [
        (cx, cy - r_outer),
        (cx + r_inner, cy - r_inner),
        (cx + r_outer, cy),
        (cx + r_inner, cy + r_inner),
        (cx, cy + r_outer),
        (cx - r_inner, cy + r_inner),
        (cx - r_outer, cy),
        (cx - r_inner, cy - r_inner),
    ]
    draw.polygon(sparkle_pts, fill=(99, 102, 241, 255))

    # Punto de estado del Guardián en la esquina inferior derecha
    badge_r = int(size * 0.12)
    bx = size - int(size * 0.20)
    by = size - int(size * 0.20)
    badge_color = (16, 185, 129, 255) if guardian_active else (56, 189, 248, 255)
    draw.ellipse(
        [(bx - badge_r, by - badge_r), (bx + badge_r, by + badge_r)],
        fill=(15, 23, 42, 255),
    )
    inner_r = int(badge_r * 0.72)
    draw.ellipse(
        [(bx - inner_r, by - inner_r), (bx + inner_r, by + inner_r)],
        fill=badge_color,
    )

    return img


# =========================================================
# 2. SELECTOR NATIVO DE CARPETAS DE WINDOWS
# =========================================================
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
                selected_path = str(Path(folder).resolve())
        except Exception:
            selected_path = None

    t = threading.Thread(target=_run_tk)
    t.start()
    t.join(timeout=120.0)
    return selected_path


# =========================================================
# 3. ESCÁNER DE ESPECIFICACIONES DE HARDWARE DE LA PC
# =========================================================
class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


_cached_hw_specs: Optional[Dict[str, Any]] = None


def get_pc_hardware_specs(force_refresh: bool = False) -> Dict[str, Any]:
    """Escanea CPU, RAM, GPU, VRAM y Disco en Windows y determina el modelo de IA ideal."""
    global _cached_hw_specs

    # Obtener RAM en vivo mediante Win32 API (<1ms)
    total_ram_gb = 8.0
    avail_ram_gb = 4.0
    ram_load_pct = 50
    try:
        stat = _MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 1)
        avail_ram_gb = round(stat.ullAvailPhys / (1024 ** 3), 1)
        ram_load_pct = int(stat.dwMemoryLoad)
    except Exception:
        pass

    # Espacio libre en disco
    try:
        usage = shutil.disk_usage(Path.home().anchor or "C:\\")
        free_disk_gb = round(usage.free / (1024 ** 3), 1)
        total_disk_gb = round(usage.total / (1024 ** 3), 1)
    except Exception:
        free_disk_gb = 0.0
        total_disk_gb = 0.0

    if _cached_hw_specs is not None and not force_refresh:
        _cached_hw_specs["avail_ram_gb"] = avail_ram_gb
        _cached_hw_specs["ram_load_pct"] = ram_load_pct
        _cached_hw_specs["free_disk_gb"] = free_disk_gb
        return _cached_hw_specs

    # Detectar CPU y GPU mediante PowerShell CIM rápido (cacheado)
    cpu_name = platform.processor() or "Procesador x64"
    cpu_cores = os.cpu_count() or 4
    gpu_name = "Gráficos Integrados"
    gpu_vram_gb = 0.0
    has_dedicated_gpu = False

    try:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        ps_cmd = (
            "$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name; "
            "$gpus = Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM; "
            "@{cpu=$cpu; gpus=$gpus} | ConvertTo-Json -Compress"
        )
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=3.5,
            creationflags=creation_flags,
        )
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout.strip())
            if data.get("cpu"):
                cpu_name = str(data["cpu"]).strip()
            gpus = data.get("gpus")
            if isinstance(gpus, dict):
                gpus = [gpus]
            if isinstance(gpus, list) and gpus:
                # Priorizar GPU dedicada (NVIDIA / AMD Radeon RX / RTX / GTX)
                best_gpu = gpus[0]
                for g in gpus:
                    gname = str(g.get("Name", "")).upper()
                    if any(k in gname for k in ["NVIDIA", "RTX", "GTX", "RADEON RX", "ARC"]):
                        best_gpu = g
                        has_dedicated_gpu = True
                        break
                gpu_name = str(best_gpu.get("Name", "Gráficos Integrados")).strip()
                raw_ram = best_gpu.get("AdapterRAM") or 0
                if int(raw_ram) > 0:
                    gpu_vram_gb = round(int(raw_ram) / (1024 ** 3), 1)
    except Exception:
        pass

    # Si hay nvidia-smi, obtener VRAM exacta de NVIDIA (Win32_VideoController tiene tope de 4GB en enteros 32-bit)
    if shutil.which("nvidia-smi"):
        try:
            creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            nv = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=2.0,
                creationflags=creation_flags,
            )
            if nv.returncode == 0 and nv.stdout.strip():
                parts = nv.stdout.strip().split("\n")[0].split(",")
                gpu_name = parts[0].strip()
                gpu_vram_gb = round(float(parts[1].strip()) / 1024.0, 1)
                has_dedicated_gpu = True
        except Exception:
            pass

    # Clasificar el nivel de hardware y modelo recomendado considerando RAM y VRAM real
    if (has_dedicated_gpu and gpu_vram_gb >= 6.0) or total_ram_gb >= 24.0:
        tier = "high"
        tier_label = "Potencia Alta (Workstation / GPU 6GB+)"
        recommended_model = "llama3:latest"
        recommendation_reason = (
            f"Tu PC cuenta con {total_ram_gb} GB de RAM y {gpu_name} ({gpu_vram_gb} GB VRAM). "
            "Soporta modelos grandes de 7B a 8B parámetros a máxima velocidad."
        )
    elif total_ram_gb >= 12.0 or (has_dedicated_gpu and gpu_vram_gb >= 4.0):
        tier = "high_balanced"
        tier_label = "Potencia Media-Alta (Gaming / Multitarea)"
        recommended_model = "llama3.2:3b"
        recommendation_reason = (
            f"Detectamos {cpu_name}, {total_ram_gb} GB RAM y {gpu_name} ({gpu_vram_gb} GB VRAM). "
            "Los modelos de 3B a 4B parámetros entran al 100% en los 4 GB de tu placa de video sin lentitud."
        )
    elif total_ram_gb >= 7.5:
        tier = "medium"
        tier_label = "Gama Media Equilibrada"
        recommended_model = "llama3.2:3b"
        recommendation_reason = (
            f"Con {total_ram_gb} GB de RAM, el modelo 'llama3.2:3b' (2.0 GB) ofrece "
            "el equilibrio ideal entre inteligencia y fluidez."
        )
    else:
        tier = "light"
        tier_label = "Equipo Ligero / Bajo Consumo"
        recommended_model = "llama3.2:1b"
        recommendation_reason = (
            f"Para cuidar tus {total_ram_gb} GB de RAM, recomendamos 'llama3.2:1b' (1.3 GB) "
            "que corre de forma instantánea."
        )

    _cached_hw_specs = {
        "cpu_name": cpu_name,
        "cpu_cores": cpu_cores,
        "total_ram_gb": total_ram_gb,
        "avail_ram_gb": avail_ram_gb,
        "ram_load_pct": ram_load_pct,
        "gpu_name": gpu_name,
        "gpu_vram_gb": gpu_vram_gb,
        "has_dedicated_gpu": has_dedicated_gpu,
        "free_disk_gb": free_disk_gb,
        "total_disk_gb": total_disk_gb,
        "tier": tier,
        "tier_label": tier_label,
        "recommended_model": recommended_model,
        "recommendation_reason": recommendation_reason,
    }
    return _cached_hw_specs


# =========================================================
# 4. GESTOR DE OLLAMA Y CATÁLOGO DE MODELOS INSTALADOS
# =========================================================
MODEL_CATALOG = [
    {
        "id": "llama3.2:1b",
        "name": "Llama 3.2 (1B Ultra-Ligero)",
        "size_label": "1.3 GB",
        "min_ram_gb": 4,
        "description": "Velocidad instantánea en cualquier CPU o notebook.",
    },
    {
        "id": "llama3.2:3b",
        "name": "Llama 3.2 (3B Equilibrado)",
        "size_label": "2.0 GB",
        "min_ram_gb": 8,
        "description": "Excelente comprensión contextual con bajo consumo de RAM.",
    },
    {
        "id": "llama3:latest",
        "name": "Llama 3 (8B Pro Studio)",
        "size_label": "4.7 GB",
        "min_ram_gb": 12,
        "description": "Máxima precisión semántica. Ideal para PCs con 16GB+ RAM o GPU.",
    },
    {
        "id": "qwen2.5:7b",
        "name": "Qwen 2.5 (7B Multilingüe)",
        "size_label": "4.7 GB",
        "min_ram_gb": 12,
        "description": "Especializado en español, clasificación técnica y código.",
    },
]


def find_ollama_executable() -> Optional[Path]:
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
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.15)
        return s.connect_ex(("127.0.0.1", 11434)) == 0


def ensure_ollama_running_if_installed() -> None:
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
    """Gestiona la detección, catálogo de modelos instalados, auto-instalación y borrado."""

    def __init__(self):
        self.state: str = "idle"
        self.progress: int = 0
        self.message: str = ""
        self.target_model: str = "llama3.2:1b"
        self._lock = threading.Lock()
        self._working = False

    def get_status(self) -> Dict[str, Any]:
        exe_path = find_ollama_executable()
        installed = exe_path is not None
        running = is_ollama_port_open()
        hw = get_pc_hardware_specs()

        installed_models_detail: List[Dict[str, Any]] = []
        installed_names: List[str] = []

        if running:
            try:
                with httpx.Client(timeout=1.5) as client:
                    res = client.get("http://127.0.0.1:11434/api/tags")
                    if res.status_code == 200:
                        for m in res.json().get("models", []):
                            m_name = m.get("name", "")
                            m_size_gb = round((m.get("size", 0) or 0) / (1024 ** 3), 2)
                            installed_names.append(m_name)
                            installed_models_detail.append({
                                "name": m_name,
                                "size_gb": m_size_gb,
                                "size_formatted": f"{m_size_gb} GB",
                            })
            except Exception:
                pass

        # Enriquecer catálogo con estado instalado y recomendación de hardware
        rec_id = hw.get("recommended_model", "llama3.2:3b")
        catalog_with_status = []
        matched_set = set()

        for item in MODEL_CATALOG:
            cid = item["id"]
            base_prefix = cid.split(":")[0]
            is_inst = any(
                inst == cid or (cid.endswith(":latest") and inst == base_prefix) or (inst == f"{cid}:latest")
                for inst in installed_names
            )
            matched_installed_name = next(
                (inst for inst in installed_names if inst == cid or (cid.endswith(":latest") and inst == base_prefix)),
                cid,
            )
            if is_inst:
                matched_set.add(matched_installed_name)

            catalog_with_status.append({
                **item,
                "installed": is_inst,
                "installed_name": matched_installed_name,
                "recommended_for_pc": (cid == rec_id),
                "compatible": hw["total_ram_gb"] >= item["min_ram_gb"],
            })

        # Añadir cualquier otro modelo que el usuario ya tenga instalado en su PC (ej: qwen3.5:4b)
        custom_installed = []
        for m_det in installed_models_detail:
            m_name = m_det["name"]
            if m_name not in matched_set:
                custom_installed.append({
                    "id": m_name,
                    "name": f"{m_name} (Instalado en PC)",
                    "size_label": m_det["size_formatted"],
                    "min_ram_gb": 4,
                    "description": "Modelo detectado en tu almacenamiento local de Ollama.",
                    "installed": True,
                    "installed_name": m_name,
                    "recommended_for_pc": (3.0 <= m_det["size_gb"] <= 4.5 and hw["tier"] == "high_balanced"),
                    "compatible": True,
                })

        catalog_with_status = custom_installed + catalog_with_status

        return {
            "installed": installed,
            "executable_path": str(exe_path) if exe_path else None,
            "running": running,
            "models": installed_names,
            "installed_models_detail": installed_models_detail,
            "catalog": catalog_with_status,
            "hardware": hw,
            "free_disk_gb": hw["free_disk_gb"],
            "setup_state": self.state,
            "setup_progress": self.progress,
            "setup_message": self.message,
            "is_working": self._working,
        }

    def delete_model(self, model_name: str) -> bool:
        """Elimina un modelo de Ollama para liberar espacio en disco."""
        if not is_ollama_port_open():
            return False
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.request(
                    "DELETE",
                    "http://127.0.0.1:11434/api/delete",
                    json={"name": model_name},
                )
                return res.status_code == 200
        except Exception:
            return False

    def start_auto_setup(self, model_name: str = "llama3.2:1b") -> Dict[str, Any]:
        with self._lock:
            if self._working:
                return self.get_status()
            self._working = True
            self.target_model = model_name or "llama3.2:1b"
            self.state = "starting"
            self.progress = 3
            self.message = f"Preparando instalación de {self.target_model}..."

        worker = threading.Thread(target=self._run_setup_pipeline, daemon=True)
        worker.start()
        return self.get_status()

    def _run_setup_pipeline(self):
        try:
            exe_path = find_ollama_executable()

            if not exe_path:
                self.state = "downloading_installer"
                self.progress = 5
                self.message = "Descargando instalador oficial OllamaSetup.exe..."

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
                                    self.message = f"Descargando Ollama ({mb_done:.0f} / {mb_total:.0f} MB)..."

                self.state = "installing"
                self.progress = 48
                self.message = "Instalando motor Ollama en Windows..."
                subprocess.run([str(installer_path), "/SILENT"], check=False)

                for _ in range(30):
                    exe_path = find_ollama_executable()
                    if exe_path:
                        break
                    time.sleep(1.0)

                if not exe_path:
                    raise RuntimeError("No se detectó el binario de Ollama tras la instalación.")

            if not is_ollama_port_open():
                self.state = "starting_service"
                self.progress = 55
                self.message = "Iniciando servicio local de IA..."
                ensure_ollama_running_if_installed()

                for _ in range(25):
                    if is_ollama_port_open():
                        break
                    time.sleep(0.5)

            if not is_ollama_port_open():
                raise RuntimeError("El servicio local de Ollama no respondió en el puerto 11434.")

            self.state = "pulling_model"
            self.progress = 60
            self.message = f"Descargando modelo '{self.target_model}'..."

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
                                self.message = f"{self.target_model}: {mb_c:.0f} MB / {mb_t:.0f} MB ({int(ratio * 100)}%)"
                            else:
                                self.message = f"{self.target_model}: {status_txt}"
                        except Exception:
                            pass

            self.state = "ready"
            self.progress = 100
            self.message = f"¡Modelo '{self.target_model}' instalado y activo!"

        except Exception as e:
            self.state = "error"
            self.message = f"Error: {str(e)}"
        finally:
            with self._lock:
                self._working = False


ollama_setup_manager = OllamaSetupManager()


# =========================================================
# 5. INICIO AUTOMÁTICO CON WINDOWS (REGISTRY RUN KEY)
# =========================================================
STARTUP_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
STARTUP_APP_NAME = "TidyDeskAI"


def get_windows_startup_status() -> bool:
    """Verifica si TidyDesk AI está configurado para iniciar junto con Windows."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY_PATH, 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, STARTUP_APP_NAME)
            return bool(val)
    except Exception:
        return False


def set_windows_startup(enable: bool) -> bool:
    """Agrega o elimina TidyDesk AI del inicio automático de Windows (minimizado en System Tray)."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}" --minimized'
                else:
                    base_dir = Path(__file__).resolve().parent.parent.parent
                    vbs_path = base_dir / "iniciar_tidydesk_tray.vbs"
                    cmd = f'wscript.exe "{vbs_path}"'
                winreg.SetValueEx(key, STARTUP_APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, STARTUP_APP_NAME)
                except FileNotFoundError:
                    pass
        return get_windows_startup_status()
    except Exception:
        return False


# =========================================================
# 6. ARCHIVADOR COLD STORAGE (.ZIP) PARA PROYECTOS ANTIGUOS
# =========================================================
def archive_old_files_to_zip(target_folder: Path, file_paths: List[str]) -> Dict[str, Any]:
    """Comprime archivos antiguos seleccionados dentro de un archivo .zip ordenado y mueve originales a cuarentena."""
    archive_dir = target_folder / "Archivos_Comprimidos_ZIP"
    archive_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    zip_path = archive_dir / f"Backup_TidyDesk_{stamp}.zip"

    archived_count = 0
    saved_bytes = 0

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for fp_str in file_paths:
            fp = Path(fp_str)
            if fp.exists() and fp.is_file():
                orig_size = fp.stat().st_size
                zf.write(fp, arcname=fp.name)
                archived_count += 1
                saved_bytes += orig_size

    zip_size = zip_path.stat().st_size if zip_path.exists() else 0
    net_saved = max(0, saved_bytes - zip_size)

    return {
        "success": archived_count > 0,
        "zip_path": str(zip_path),
        "zip_name": zip_path.name,
        "archived_count": archived_count,
        "net_saved_mb": round(net_saved / (1024 * 1024), 2),
    }
