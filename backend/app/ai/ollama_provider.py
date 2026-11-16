import json
import socket
import httpx
from typing import List, Dict, Any
from app.ai.base import AIProvider
from app.ai.rules_provider import SmartRulesProvider
from app.config import DEFAULT_OLLAMA_URL, DEFAULT_OLLAMA_MODEL
from app.schemas.organize import PlanItem

SYSTEM_PROMPT = """Eres TidyDesk AI, un asistente senior especializado en organización inteligente de archivos en Windows.
Tu misión es clasificar una lista de archivos desordenados en carpetas lógicas y temáticas basadas en el contexto del usuario.
Reglas:
1. Las carpetas deben ser claras y humanas (ej: 'Facultad / Programación II', 'Finanzas / Facturas', 'Instaladores', 'Imágenes / Capturas', 'Documentos').
2. Devuelve ÚNICAMENTE un array JSON válido sin texto adicional, sin markdown y sin explicaciones extra.
Formato de salida esperado:
[
  {
    "file_id": "id_del_archivo",
    "suggested_folder": "Nombre de la Carpeta",
    "suggested_name": "nombre_limpio.ext",
    "reason": "Explicación breve de 1 frase del por qué"
  }
]
"""

class OllamaProvider(AIProvider):
    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL):
        self.base_url = base_url.rstrip("/")

    async def is_available(self) -> bool:
        """Verifica si Ollama está en ejecución local de forma instantánea sin bloquear."""
        import select

        # 1. Comprobación no bloqueante con select (máximo 100ms)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(False)
            try:
                s.connect(("127.0.0.1", 11434))
                s.close()
                is_open = True
            except BlockingIOError:
                _, writable, _ = select.select([], [s], [], 0.1)
                s.close()
                is_open = len(writable) > 0
            except Exception:
                s.close()
                is_open = False
        except Exception:
            is_open = False

        if not is_open:
            return False

        # 2. Si el puerto responde, validar API HTTP
        try:
            timeout = httpx.Timeout(0.5, connect=0.3)
            async with httpx.AsyncClient(timeout=timeout) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def get_available_models(self) -> List[str]:
        """Obtiene los modelos instalados en Ollama."""
        try:
            async with httpx.AsyncClient(timeout=2.5) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    return models
        except Exception:
            pass
        return []

    async def generate_plan(
        self,
        files: List[Dict[str, Any]],
        model: str | None = None,
        custom_instructions: str | None = None
    ) -> List[PlanItem]:
        selected_model = model or DEFAULT_OLLAMA_MODEL

        # Simplificar lista de archivos para reducir tokens y acelerar la inferencia
        file_payload = [
            {
                "file_id": f.get("id"),
                "name": f.get("name"),
                "extension": f.get("extension"),
                "size": f.get("size_formatted"),
            }
            for f in files
        ]

        prompt_user = f"Clasifica los siguientes archivos según las reglas:\n{json.dumps(file_payload, ensure_ascii=False)}"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": selected_model,
                        "system": SYSTEM_PROMPT,
                        "prompt": prompt_user,
                        "format": "json",
                        "stream": False,
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    raw_response = data.get("response", "").strip()
                    parsed = json.loads(raw_response)

                    # Si el modelo devuelve un diccionario envolvente, extraer lista
                    if isinstance(parsed, dict):
                        for val in parsed.values():
                            if isinstance(val, list):
                                parsed = val
                                break

                    # Mapear respuesta
                    file_map = {f.get("id"): f for f in files}
                    plan_items: List[PlanItem] = []

                    for item in parsed:
                        f_id = item.get("file_id")
                        orig_file = file_map.get(f_id)
                        if orig_file:
                            plan_items.append(
                                PlanItem(
                                    file_id=f_id,
                                    original_path=orig_file.get("path"),
                                    original_name=orig_file.get("name"),
                                    suggested_folder=item.get("suggested_folder", "Varios"),
                                    suggested_name=item.get("suggested_name", orig_file.get("name")),
                                    reason=item.get("reason", "Clasificado por Ollama"),
                                    selected=True,
                                )
                            )

                    if plan_items:
                        return plan_items
        except Exception:
            pass

        # Fallback de seguridad si Ollama falla o produce JSON corrupto
        rules_provider = SmartRulesProvider()
        return await rules_provider.generate_plan(files)
