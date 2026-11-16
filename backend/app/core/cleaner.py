import hashlib
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from app.core.scanner import scan_directory, format_size, resolve_target_folder
from app.core.history import save_transaction
from app.core.organizer import resolve_unique_path
from app.schemas.scan import FileItem
from app.schemas.cleaner import (
    DuplicateGroup,
    OldInstaller,
    AuditCleanResponse,
    CleanActionRequest,
    CleanActionResponse,
)
from app.schemas.organize import TransactionRecord, FileMoveRecord

def calculate_sha256(file_path: Path, max_bytes: int = 50 * 1024 * 1024) -> str:
    """Calcula el hash SHA-256 leyendo el archivo en bloques de 64KB."""
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            total_read = 0
            while chunk := f.read(65536):
                sha256.update(chunk)
                total_read += len(chunk)
                # Para archivos masivos (+50MB), leer los primeros 50MB es suficiente para fingerprint certero
                if total_read >= max_bytes:
                    break
        return sha256.hexdigest()
    except Exception:
        return ""

def audit_clean_directory(target_path: Path, days_threshold: int = 30) -> AuditCleanResponse:
    """Audita duplicados idénticos por SHA-256 e instaladores viejos."""
    scan_res = scan_directory(target_path, include_shortcuts=False)
    files = scan_res.files

    # 1. Agrupar por tamaño primero (optimización para no hashear todo el disco)
    size_map: Dict[int, List[FileItem]] = {}
    for f in files:
        if f.size_bytes > 0:
            size_map.setdefault(f.size_bytes, []).append(f)

    # 2. Hashear solo los que comparten tamaño exacto
    duplicate_groups: List[DuplicateGroup] = []
    total_duplicates_count = 0
    duplicates_waste_bytes = 0

    for size, file_group in size_map.items():
        if len(file_group) < 2:
            continue

        hash_map: Dict[str, List[FileItem]] = {}
        for item in file_group:
            h = calculate_sha256(Path(item.path))
            if h:
                hash_map.setdefault(h, []).append(item)

        for h, matching_files in hash_map.items():
            if len(matching_files) > 1:
                # El más antiguo o con nombre más corto se considera el original
                matching_files.sort(key=lambda x: len(x.name))
                original = matching_files[0]
                duplicates = matching_files[1:]

                duplicate_groups.append(
                    DuplicateGroup(
                        hash_sha256=h,
                        size_bytes=size,
                        size_formatted=format_size(size),
                        original=original,
                        duplicates=duplicates,
                    )
                )
                total_duplicates_count += len(duplicates)
                duplicates_waste_bytes += size * len(duplicates)

    # 3. Detectar instaladores (.exe / .msi) con más de 'days_threshold' días
    old_installers: List[OldInstaller] = []
    total_old_installers_bytes = 0
    now = datetime.now()

    for f in files:
        if f.extension in [".exe", ".msi"]:
            try:
                stat = Path(f.path).stat()
                mod_dt = datetime.fromtimestamp(stat.st_mtime)
                days_old = (now - mod_dt).days
                if days_old >= days_threshold:
                    old_installers.append(OldInstaller(file=f, days_old=days_old))
                    total_old_installers_bytes += f.size_bytes
            except Exception:
                continue

    old_installers.sort(key=lambda x: x.days_old, reverse=True)

    total_recoverable_bytes = duplicates_waste_bytes + total_old_installers_bytes

    return AuditCleanResponse(
        duplicate_groups=duplicate_groups,
        total_duplicates_count=total_duplicates_count,
        duplicates_waste_bytes=duplicates_waste_bytes,
        duplicates_waste_formatted=format_size(duplicates_waste_bytes),
        old_installers=old_installers,
        total_old_installers_bytes=total_old_installers_bytes,
        total_old_installers_formatted=format_size(total_old_installers_bytes),
        total_recoverable_formatted=format_size(total_recoverable_bytes),
    )

def execute_clean_action(target_path: Path, request: CleanActionRequest) -> CleanActionResponse:
    """Mueve los duplicados o instaladores seleccionados a una carpeta segura con opción de Rollback."""
    scan_res = scan_directory(target_path, include_shortcuts=True)
    file_map = {f.id: f for f in scan_res.files}

    dest_dir = target_path / "_Limpieza_TidyDesk"
    dest_dir.mkdir(parents=True, exist_ok=True)

    tx_id = f"clean_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    move_records: List[FileMoveRecord] = []
    errors: List[str] = []
    freed_bytes = 0
    cleaned_count = 0

    for f_id in request.file_ids_to_clean:
        file_item = file_map.get(f_id)
        if not file_item:
            continue

        src_path = Path(file_item.path)
        if not src_path.exists():
            continue

        try:
            target_dest = resolve_unique_path(dest_dir / src_path.name)
            shutil.move(str(src_path), str(target_dest))

            move_records.append(
                FileMoveRecord(
                    file_id=file_item.id,
                    original_path=str(src_path),
                    new_path=str(target_dest),
                    file_name=src_path.name,
                )
            )
            freed_bytes += file_item.size_bytes
            cleaned_count += 1
        except Exception as e:
            errors.append(f"No se pudo limpiar {src_path.name}: {str(e)}")

    if move_records:
        tx_record = TransactionRecord(
            transaction_id=tx_id,
            timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            target_folder=str(target_path),
            moves=move_records,
            reverted=False,
        )
        save_transaction(tx_record)

    return CleanActionResponse(
        transaction_id=tx_id,
        cleaned_count=cleaned_count,
        freed_space_formatted=format_size(freed_bytes),
        success=len(errors) == 0 and cleaned_count > 0,
        errors=errors,
    )
