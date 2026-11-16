from pathlib import Path
import os
import hashlib
from datetime import datetime
from typing import List, Tuple
from app.config import (
    DESKTOP_DIR,
    DOWNLOADS_DIR,
    BLACKLIST_EXTENSIONS,
    BLACKLIST_FILENAMES,
)
from app.schemas.scan import FileItem, ScanResponse

def format_size(size_bytes: int) -> str:
    """Formatea bytes a formato legible para humanos."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def generate_file_id(path: Path) -> str:
    """Genera un hash determinista para identificar el archivo."""
    return hashlib.md5(str(path.resolve()).encode("utf-8")).hexdigest()[:12]

def resolve_target_folder(folder_type: str, custom_path: str | None = None) -> Path:
    """Obtiene la ruta absoluta segura de la carpeta a escanear."""
    if folder_type == "desktop":
        target = DESKTOP_DIR
    elif folder_type == "downloads":
        target = DOWNLOADS_DIR
    elif folder_type == "custom" and custom_path:
        target = Path(custom_path).resolve()
    else:
        target = DESKTOP_DIR

    if not target.exists() or not target.is_dir():
        raise FileNotFoundError(f"La carpeta '{target}' no existe o no es accesible.")
    return target

def is_safe_to_organize(file_path: Path, include_shortcuts: bool = False) -> Tuple[bool, str]:
    """Verifica si un archivo puede ser organizado sin comprometer el sistema."""
    name_lower = file_path.name.lower()
    suffix_lower = file_path.suffix.lower()

    # Filtro 1: Nombres del sistema inmutables
    if name_lower in BLACKLIST_FILENAMES:
        return False, "Nombre en lista negra del sistema"

    # Filtro 2: Accesos directos (.lnk / .url)
    if suffix_lower in [".lnk", ".url"]:
        if include_shortcuts:
            return True, "Acceso directo habilitado por usuario"
        return False, "Acceso directo protegido (.lnk)"

    # Filtro 3: Extensiones prohibidas de sistema
    if suffix_lower in BLACKLIST_EXTENSIONS:
        return False, f"Extensión protegida de sistema ({suffix_lower})"

    # Filtro 4: Archivos o carpetas ocultas en Windows
    if file_path.name.startswith("."):
        return False, "Archivo oculto o de configuración"

    # Filtro 5: Es un directorio
    if file_path.is_dir():
        return False, "Es un directorio existente"

    return True, "Seguro"

def scan_directory(target_path: Path, include_shortcuts: bool = False) -> ScanResponse:
    """Escanea el directorio raíz especificado (sin descender recursivamente en carpetas ya creadas)."""
    organizable_files: List[FileItem] = []
    ignored_count = 0
    total_found = 0

    try:
        entries = list(target_path.iterdir())
    except PermissionError as e:
        raise PermissionError(f"Sin permisos para leer el directorio {target_path}: {e}")

    for entry in entries:
        # Solo analizamos archivos en la raíz de la carpeta seleccionada
        if entry.is_dir():
            continue

        total_found += 1
        safe, _ = is_safe_to_organize(entry, include_shortcuts=include_shortcuts)

        if not safe:
            ignored_count += 1
            continue

        try:
            stat = entry.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
            file_item = FileItem(
                id=generate_file_id(entry),
                name=entry.name,
                path=str(entry.resolve()),
                extension=entry.suffix.lower(),
                size_bytes=stat.st_size,
                size_formatted=format_size(stat.st_size),
                modified_at=mod_time,
                is_organizable=True,
            )
            organizable_files.append(file_item)
        except (PermissionError, FileNotFoundError):
            ignored_count += 1
            continue

    # Ordenar por fecha o tamaño
    organizable_files.sort(key=lambda x: x.size_bytes, reverse=True)

    return ScanResponse(
        target_folder=str(target_path.resolve()),
        target_folder_name=target_path.name,
        total_found=total_found,
        organizable_count=len(organizable_files),
        ignored_count=ignored_count,
        files=organizable_files,
    )
