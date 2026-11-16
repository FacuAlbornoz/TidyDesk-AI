import json
import os
import re
import httpx
from typing import List, Dict, Any
from app.ai.base import AIProvider
from app.ai.rules_provider import SmartRulesProvider
from app.config import DEFAULT_GEMINI_MODEL
from app.schemas.organize import PlanItem

SYSTEM_INSTRUCTION = """Eres TidyDesk AI, un asistente senior especializado en organización inteligente de archivos en Windows.
Tu misión es clasificar una lista de archivos desordenados en carpetas lógicas y temáticas basadas en el contexto del usuario (facultad, finanzas, descargas, etc.).
Debes devolver ÚNICAMENTE un array JSON válido con la siguiente estructura:
[
  {
    "file_id": "string",
    "suggested_folder": "string",
    "suggested_name": "string",
    "reason": "string"
  }
]
"""

class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    async def is_available(self) -> bool:
        """Verifica si se cuenta con una API Key configurada."""
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def generate_plan(
        self,
        files: List[Dict[str, Any]],
        model: str | None = None,
        custom_instructions: str | None = None
    ) -> List[PlanItem]:
        if not await self.is_available():
            # Sin API key: fallback al motor de reglas inteligente
            rules_provider = SmartRulesProvider()
            return await rules_provider.generate_plan(files)

        selected_model = model or DEFAULT_GEMINI_MODEL

        file_payload = [
            {
                "file_id": f.get("id"),
                "name": f.get("name"),
                "extension": f.get("extension"),
                "size": f.get("size_formatted"),
            }
            for f in files
        ]

        prompt_text = f"{SYSTEM_INSTRUCTION}\n\nArchivos a organizar:\n{json.dumps(file_payload, ensure_ascii=False)}"

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent?key={self.api_key}"

        request_body = {
            "contents": [
                {
                    "parts": [{"text": prompt_text}]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(url, json=request_body)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        text_response = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        parsed = json.loads(text_response)

                        if isinstance(parsed, dict):
                            for val in parsed.values():
                                if isinstance(val, list):
                                    parsed = val
                                    break

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
                                        reason=item.get("reason", "Clasificado por Gemini AI"),
                                        selected=True,
                                    )
                                )

                        if plan_items:
                            return plan_items
        except Exception:
            pass

        # Fallback de seguridad
        rules_provider = SmartRulesProvider()
        return await rules_provider.generate_plan(files)
