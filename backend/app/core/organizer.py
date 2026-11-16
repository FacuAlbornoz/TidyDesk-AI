import shutil
import uuid
import re
from datetime import datetime
from pathlib import Path
from typing import List
from app.core.history import save_transaction, get_transaction, mark_transaction_reverted
from app.schemas.organize import (
    PlanItem,
    ExecuteResponse,
    RollbackResponse,
    TransactionRecord,
    FileMoveRecord,
)

def sanitize_filename(filename: str) -> str:
    """Elimina o reemplaza caracteres no válidos para nombres de archivo en Windows."""
    # En Windows no se permiten: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename).strip()
    # Los archivos en Windows no pueden terminar con punto o espacio
    sanitized = sanitized.rstrip(". ")
    return sanitized or "archivo_sin_nombre"

def resolve_destination_dir(target_folder: Path, suggested_folder: str) -> Path:
    """Limpia los segmentos de ruta dividiendo por barras y eliminando espacios iniciales o finales.
    Esto previene el error [WinError 123] de Windows cuando una carpeta termina con un espacio ('Facultad / Estudio').
    """
    clean_parts = [part.strip() for part in re.split(r"[/\\]+", suggested_folder) if part.strip()]
    if not clean_parts:
        return target_folder / "Varios"
    # Sanitizar cada segmento
    safe_parts = [re.sub(r'[<>:"/\\|?*]', '_', p).strip().rstrip(". ") for p in clean_parts]
    return target_folder.joinpath(*safe_parts)

def resolve_unique_path(dest_path: Path) -> Path:
    """Evita sobrescribir archivos si ya existe uno en el destino añadiendo sufijo (_1, _2, etc.)."""
    if not dest_path.exists():
        return dest_path

    parent = dest_path.parent
    stem = dest_path.stem
    suffix = dest_path.suffix
    counter = 1

    while True:
        candidate = parent / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def execute_plan(target_folder: Path, items: List[PlanItem]) -> ExecuteResponse:
    """Ejecuta los movimientos de archivos aprobados por el usuario y genera una transacción."""
    tx_id = f"tx_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
    move_records: List[FileMoveRecord] = []
    errors: List[str] = []
    moved_count = 0
    skipped_count = 0

    for item in items:
        if not item.selected:
            skipped_count += 1
            continue

        src_path = Path(item.original_path).resolve()
        if not src_path.exists():
            errors.append(f"El archivo original ya no existe: {src_path.name}")
            skipped_count += 1
            continue

        # Crear subdirectorio de destino seguro y sin espacios que rompan NTFS
        dest_dir = resolve_destination_dir(target_folder, item.suggested_folder)

        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            # Limpiar nombre sugerido y resolver colisiones
            base_name = item.suggested_name.strip() or src_path.name
            clean_name = sanitize_filename(base_name)
            dest_candidate = dest_dir / clean_name
            final_dest = resolve_unique_path(dest_candidate)

            # Mover archivo
            shutil.move(str(src_path), str(final_dest))

            move_records.append(
                FileMoveRecord(
                    file_id=item.file_id,
                    original_path=str(src_path),
                    new_path=str(final_dest),
                    file_name=src_path.name,
                )
            )
            moved_count += 1
        except Exception as e:
            errors.append(f"Error al mover {src_path.name}: {str(e)}")

    # Guardar transacción si hubo al menos un movimiento
    if move_records:
        tx_record = TransactionRecord(
            transaction_id=tx_id,
            timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            target_folder=str(target_folder),
            moves=move_records,
            reverted=False,
        )
        save_transaction(tx_record)

    return ExecuteResponse(
        transaction_id=tx_id,
        timestamp=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        moved_count=moved_count,
        skipped_count=skipped_count,
        errors=errors,
        success=len(errors) == 0 and moved_count > 0,
    )

def rollback_transaction(transaction_id: str) -> RollbackResponse:
    """Devuelve todos los archivos de una transacción a su ubicación original exacta."""
    tx = get_transaction(transaction_id)
    if not tx:
        return RollbackResponse(
            transaction_id=transaction_id,
            restored_count=0,
            errors=["Transacción no encontrada en el historial."],
            success=False,
        )

    if tx.get("reverted"):
        return RollbackResponse(
            transaction_id=transaction_id,
            restored_count=0,
            errors=["Esta transacción ya fue revertida previamente."],
            success=False,
        )

    moves = tx.get("moves", [])
    restored_count = 0
    errors: List[str] = []
    folders_to_check = set()

    for move in moves:
        current_path = Path(move.get("new_path"))
        original_path = Path(move.get("original_path"))

        if not current_path.exists():
            errors.append(f"No se encontró el archivo en su ruta actual: {current_path.name}")
            continue

        try:
            # Asegurar que el directorio original existe
            original_path.parent.mkdir(parents=True, exist_ok=True)
            # Si el destino original ya estuviese ocupado, resolver colisión
            target_restore = resolve_unique_path(original_path)
            shutil.move(str(current_path), str(target_restore))
            restored_count += 1
            folders_to_check.add(current_path.parent)
        except Exception as e:
            errors.append(f"Error al restaurar {current_path.name}: {str(e)}")

    # Limpiar carpetas que hayan quedado vacías
    for folder in folders_to_check:
        try:
            if folder.exists() and not any(folder.iterdir()):
                folder.rmdir()
        except Exception:
            pass

    if restored_count > 0:
        mark_transaction_reverted(transaction_id)

    return RollbackResponse(
        transaction_id=transaction_id,
        restored_count=restored_count,
        errors=errors,
        success=len(errors) == 0,
    )
