from pydantic import BaseModel, Field
from typing import List, Optional

class PlanItem(BaseModel):
    file_id: str
    original_path: str
    original_name: str
    suggested_folder: str = Field(..., description="Carpeta relativa de destino (ej: 'Documentos/Facturas')")
    suggested_name: str = Field(..., description="Nombre sugerido (limpio o igual)")
    reason: str = Field(..., description="Explicación breve de la clasificación dada por la IA")
    selected: bool = Field(True, description="Si el usuario confirma que desea mover este archivo")

class PlanRequest(BaseModel):
    target_folder: str
    provider: str = Field("ollama", description="'ollama', 'gemini' o 'smart_rules'")
    model: Optional[str] = Field(None, description="Nombre del modelo (ej: 'llama3', 'gemini-1.5-flash')")
    api_key: Optional[str] = Field(None, description="API Key si se utiliza Gemini")
    files: List[dict] = Field(..., description="Lista de archivos escaneados")
    enable_smart_rename: bool = Field(True, description="Si se activa el renombrado multimodal para imágenes y PDFs")

class PlanResponse(BaseModel):
    provider_used: str
    model_used: str
    total_planned: int
    items: List[PlanItem]

class ExecuteRequest(BaseModel):
    target_folder: str
    items: List[PlanItem]

class FileMoveRecord(BaseModel):
    file_id: str
    original_path: str
    new_path: str
    file_name: str

class TransactionRecord(BaseModel):
    transaction_id: str
    timestamp: str
    target_folder: str
    moves: List[FileMoveRecord]
    reverted: bool = False

class ExecuteResponse(BaseModel):
    transaction_id: str
    timestamp: str
    moved_count: int
    skipped_count: int
    errors: List[str] = []
    success: bool

class RollbackRequest(BaseModel):
    transaction_id: str

class RollbackResponse(BaseModel):
    transaction_id: str
    restored_count: int
    errors: List[str] = []
    success: bool
