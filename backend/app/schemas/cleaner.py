from pydantic import BaseModel, Field
from typing import List
from app.schemas.scan import FileItem

class DuplicateGroup(BaseModel):
    hash_sha256: str
    size_bytes: int
    size_formatted: str
    original: FileItem
    duplicates: List[FileItem]

class OldInstaller(BaseModel):
    file: FileItem
    days_old: int

class AuditCleanResponse(BaseModel):
    duplicate_groups: List[DuplicateGroup]
    total_duplicates_count: int
    duplicates_waste_bytes: int
    duplicates_waste_formatted: str
    old_installers: List[OldInstaller]
    total_old_installers_bytes: int
    total_old_installers_formatted: str
    total_recoverable_formatted: str

class CleanActionRequest(BaseModel):
    target_folder: str
    file_ids_to_clean: List[str] = Field(..., description="IDs de archivos duplicados o instaladores viejos a limpiar")
    destination_action: str = Field("archive", description="'archive' (mover a subcarpeta de limpieza) o 'delete'")

class CleanActionResponse(BaseModel):
    transaction_id: str
    cleaned_count: int
    freed_space_formatted: str
    success: bool
    errors: List[str] = []
