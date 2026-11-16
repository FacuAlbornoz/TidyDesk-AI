from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import (
    DESKTOP_DIR,
    DOWNLOADS_DIR,
    FRONTEND_DIR,
    DEFAULT_OLLAMA_MODEL,
    DEFAULT_GEMINI_MODEL,
)
from app.schemas.scan import ScanRequest, ScanResponse
from app.schemas.organize import (
    PlanRequest,
    PlanResponse,
    ExecuteRequest,
    ExecuteResponse,
    RollbackRequest,
    RollbackResponse,
)
from app.core.scanner import scan_directory, resolve_target_folder
from app.core.organizer import execute_plan, rollback_transaction
from app.core.history import load_history
from app.ai.ollama_provider import OllamaProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.rules_provider import SmartRulesProvider

app = FastAPI(
    title="TidyDesk AI API",
    description="Motor backend de organización inteligente de archivos con IA y Rollback",
    version="1.0.0",
)

# CORS Middleware para desarrollo y consumo desde cliente local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    """Verifica el estado del backend y la disponibilidad de los proveedores de IA."""
    ollama = OllamaProvider()
    ollama_ok = await ollama.is_available()
    ollama_models = await ollama.get_available_models() if ollama_ok else []

    return {
        "status": "healthy",
        "system": "TidyDesk AI v1.0",
        "providers": {
            "ollama": {
                "available": ollama_ok,
                "models": ollama_models,
                "default_model": DEFAULT_OLLAMA_MODEL,
            },
            "gemini": {
                "available": True,  # Requiere API Key proporcionada por el usuario
                "default_model": DEFAULT_GEMINI_MODEL,
            },
            "smart_rules": {
                "available": True,
                "description": "Clasificador heurístico sin latencia",
            },
        },
        "default_folders": {
            "desktop": str(DESKTOP_DIR),
            "downloads": str(DOWNLOADS_DIR),
        },
    }

@app.post("/api/scan", response_model=ScanResponse)
async def scan_folder(request: ScanRequest):
    """Escanea el directorio objetivo aplicando las guardas de seguridad."""
    try:
        target = resolve_target_folder(request.folder_type, request.custom_path)
        return scan_directory(target, include_shortcuts=request.include_shortcuts)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado durante el escaneo: {str(e)}")

@app.post("/api/plan", response_model=PlanResponse)
async def create_organization_plan(request: PlanRequest):
    """Genera la propuesta de organización con el proveedor de IA seleccionado (Dry-Run)."""
    if not request.files:
        raise HTTPException(status_code=400, detail="No se proporcionaron archivos para clasificar.")

    provider_name = request.provider.lower()
    model_used = request.model or "default"

    if provider_name == "ollama":
        provider = OllamaProvider()
        if not await provider.is_available():
            # Si el usuario eligió Ollama pero está apagado, fallback a reglas
            provider = SmartRulesProvider()
            provider_name = "smart_rules (Fallback por Ollama inactivo)"
            model_used = "heurístico"
        else:
            model_used = request.model or DEFAULT_OLLAMA_MODEL
    elif provider_name == "gemini":
        provider = GeminiProvider(api_key=request.api_key)
        model_used = request.model or DEFAULT_GEMINI_MODEL
    else:
        provider = SmartRulesProvider()
        provider_name = "smart_rules"
        model_used = "heurístico"

    try:
        items = await provider.generate_plan(request.files, model=model_used)
        return PlanResponse(
            provider_used=provider_name,
            model_used=model_used,
            total_planned=len(items),
            items=items,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar el plan de organización: {str(e)}")

@app.post("/api/execute", response_model=ExecuteResponse)
async def execute_movements(request: ExecuteRequest):
    """Ejecuta los movimientos de archivos aprobados y registra la transacción para Rollback."""
    target_path = Path(request.target_folder).resolve()
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="La carpeta objetivo no existe.")

    try:
        result = execute_plan(target_path, request.items)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error crítico durante la ejecución: {str(e)}")

@app.get("/api/history")
async def get_history():
    """Retorna el historial de transacciones realizadas."""
    return {"transactions": load_history()}

@app.post("/api/rollback", response_model=RollbackResponse)
async def rollback(request: RollbackRequest):
    """Revierte una transacción devolviendo todos los archivos a su lugar original."""
    try:
        result = rollback_transaction(request.transaction_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al revertir la transacción: {str(e)}")

# Montar frontend para servir la aplicación web en http://localhost:8000
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
