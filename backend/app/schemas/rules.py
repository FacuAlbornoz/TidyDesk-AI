from pydantic import BaseModel, Field
from typing import List

class CustomRule(BaseModel):
    id: str = Field(..., description="Identificador único de la regla")
    name: str = Field(..., description="Nombre descriptivo (ej: 'Archivos 3D')")
    pattern_type: str = Field("extension", description="'extension' o 'keyword'")
    patterns: List[str] = Field(..., description="Lista de extensiones (.stl, .pdf) o palabras clave")
    destination_path: str = Field(..., description="Ruta de destino absoluta o relativa")
    enabled: bool = Field(True, description="Estado de activación de la regla")

class CustomRuleCreate(BaseModel):
    name: str
    pattern_type: str
    patterns: List[str]
    destination_path: str
    enabled: bool = True
