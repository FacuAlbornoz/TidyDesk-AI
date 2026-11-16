from pydantic import BaseModel, Field
from typing import List, Optional

class GuardianConfig(BaseModel):
    enabled: bool = Field(False, description="Estado activo/inactivo del Modo Guardián")
    folder_type: str = Field("downloads", description="'downloads', 'desktop' o 'custom'")
    custom_path: Optional[str] = Field(None, description="Ruta absoluta si folder_type es 'custom'")
    mode: str = Field(
        "all",
        description="'custom_only' (solo reglas personalizadas) o 'all' (reglas + clasificación inteligente)"
    )
    enable_smart_rename: bool = Field(True, description="Renombrar automáticamente PDFs e imágenes al detectar")
    windows_notifications: bool = Field(True, description="Mostrar notificación nativa de Windows al organizar")

class GuardianEvent(BaseModel):
    event_id: str
    timestamp: str
    original_name: str
    new_name: str
    destination_folder: str
    reason: str
    transaction_id: str
    reverted: bool = False

class GuardianStatusResponse(BaseModel):
    running: bool
    watched_path: str
    config: GuardianConfig
    events: List[GuardianEvent] = []
    total_processed_session: int = 0
