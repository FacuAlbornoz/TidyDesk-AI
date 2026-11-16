from pydantic import BaseModel, Field
from typing import List, Optional

class FileItem(BaseModel):
    id: str = Field(..., description="Identificador único del archivo (hash de ruta)")
    name: str = Field(..., description="Nombre del archivo con extensión")
    path: str = Field(..., description="Ruta absoluta completa")
    extension: str = Field(..., description="Extensión en minúsculas (.pdf, .lnk, .png, etc.)")
    size_bytes: int = Field(..., description="Tamaño exacto en bytes")
    size_formatted: str = Field(..., description="Tamaño legible (KB, MB, GB)")
    modified_at: str = Field(..., description="Fecha de última modificación formateada")
    is_organizable: bool = Field(True, description="Indica si es elegible para ser organizado")

class ScanRequest(BaseModel):
    folder_type: str = Field("desktop", description="'desktop', 'downloads' o 'custom'")
    custom_path: Optional[str] = Field(None, description="Ruta personalizada si folder_type es 'custom'")
    include_shortcuts: bool = Field(False, description="Si es True, permite organizar accesos directos (.lnk y .url)")

class ScanResponse(BaseModel):
    target_folder: str
    target_folder_name: str
    total_found: int
    organizable_count: int
    ignored_count: int
    files: List[FileItem]
