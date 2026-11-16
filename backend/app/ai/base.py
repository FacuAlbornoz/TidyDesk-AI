from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas.organize import PlanItem

class AIProvider(ABC):
    """Contrato base para cualquier proveedor de inteligencia artificial."""

    @abstractmethod
    async def is_available(self) -> bool:
        """Verifica si el servicio de IA está accesible y listo para recibir peticiones."""
        pass

    @abstractmethod
    async def generate_plan(
        self,
        files: List[Dict[str, Any]],
        model: str | None = None,
        custom_instructions: str | None = None
    ) -> List[PlanItem]:
        """Analiza la lista de archivos y genera las sugerencias de organización."""
        pass
