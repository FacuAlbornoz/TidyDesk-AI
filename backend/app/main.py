from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
import io

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
from app.schemas.rules import CustomRule, CustomRuleCreate
from app.schemas.cleaner import AuditCleanResponse, CleanActionRequest, CleanActionResponse
from app.schemas.guardian import GuardianConfig, GuardianStatusResponse
from app.core.scanner import scan_directory, resolve_target_folder
from app.core.organizer import execute_plan, rollback_transaction
from app.core.history import load_history
from app.core.rules_manager import load_rules, create_rule, delete_rule, toggle_rule
from app.core.cleaner import audit_clean_directory, execute_clean_action
from app.core.multimodal import apply_multimodal_renaming
from app.core.guardian import guardian_manager
from app.core.system_utils import (
    pick_folder_dialog,
    ollama_setup_manager,
    ensure_ollama_running_if_installed,
)
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
    """Verifica el estado del backend y despierta Ollama automáticamente si está instalado."""
    ensure_ollama_running_if_installed()
    ollama = OllamaProvider()
    ollama_ok = await ollama.is_available()
    ollama_models = await ollama.get_available_models() if ollama_ok else []

    return {
        "status": "healthy",
        "system": "TidyDesk AI v2.1",
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
        if request.enable_smart_rename:
            items = await apply_multimodal_renaming(
                items,
                provider=provider_name,
                model=model_used,
                api_key=request.api_key
            )
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

# ==========================================
# ENDPOINTS: REGLAS PERSONALIZADAS (V1.1)
# ==========================================
@app.get("/api/rules", response_model=list[CustomRule])
async def get_rules():
    """Retorna las reglas personalizadas configuradas."""
    return load_rules()

@app.post("/api/rules", response_model=CustomRule)
async def add_rule(rule_data: CustomRuleCreate):
    """Crea una nueva regla personalizada."""
    return create_rule(rule_data)

@app.delete("/api/rules/{rule_id}")
async def remove_rule(rule_id: str):
    """Elimina una regla personalizada."""
    deleted = delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"success": True, "rule_id": rule_id}

@app.post("/api/rules/{rule_id}/toggle", response_model=CustomRule)
async def toggle_rule_status(rule_id: str):
    """Activa o desactiva una regla personalizada."""
    rule = toggle_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return rule

# ==========================================
# ENDPOINTS: LIMPIEZA INTELIGENTE Y DUPLICADOS (V1.2)
# ==========================================
@app.post("/api/cleaner/audit", response_model=AuditCleanResponse)
async def audit_cleaning(request: ScanRequest):
    """Audita archivos duplicados por hash SHA-256 e instaladores antiguos."""
    try:
        target = resolve_target_folder(request.folder_type, request.custom_path)
        return audit_clean_directory(target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en auditoría de limpieza: {str(e)}")

@app.post("/api/cleaner/execute", response_model=CleanActionResponse)
async def execute_cleaning(request: CleanActionRequest):
    """Ejecuta la limpieza segura de duplicados o instaladores antiguos con Rollback."""
    target_path = Path(request.target_folder).resolve()
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="La carpeta objetivo no existe.")
    try:
        return execute_clean_action(target_path, request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar limpieza: {str(e)}")

# ==========================================
# ENDPOINTS: MODO GUARDIÁN EN SEGUNDO PLANO (V1.4)
# ==========================================

@app.get("/api/guardian/status", response_model=GuardianStatusResponse)
async def get_guardian_status():
    """Devuelve el estado actual del demonio Watchdog y los últimos archivos auto-organizados."""
    return guardian_manager.get_status()

@app.post("/api/guardian/toggle", response_model=GuardianStatusResponse)
async def toggle_guardian_mode(config: GuardianConfig):
    """Activa, actualiza o detiene el Modo Guardián en tiempo real."""
    try:
        if config.enabled:
            return guardian_manager.start(config)
        else:
            return guardian_manager.stop()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al configurar Modo Guardián: {str(e)}")

@app.post("/api/guardian/clear", response_model=GuardianStatusResponse)
async def clear_guardian_events():
    """Limpia la bitácora de eventos de la sesión actual del Guardián."""
    return guardian_manager.clear_events()

# ==========================================
# ENDPOINTS: INTEGRACIÓN NATIVA WINDOWS & AUTO-SETUP OLLAMA (V2.1)
# ==========================================

class OllamaAutoSetupRequest(BaseModel):
    model: str = "llama3.2:1b"

@app.get("/api/system/pick-folder")
async def pick_native_windows_folder(title: str = "Seleccionar carpeta — TidyDesk AI"):
    """Abre el diálogo nativo de Windows Explorer para elegir cualquier carpeta sin escribir rutas."""
    chosen = pick_folder_dialog(title)
    if not chosen:
        return {"selected": False, "path": "", "name": ""}
    p = Path(chosen)
    return {"selected": True, "path": str(p), "name": p.name or str(p)}

@app.get("/api/ollama/setup-status")
async def get_ollama_setup_status():
    """Consulta si Ollama está instalado en el sistema, el espacio en disco y el progreso de descarga."""
    return ollama_setup_manager.get_status()

@app.post("/api/ollama/auto-setup")
async def trigger_ollama_auto_setup(req: OllamaAutoSetupRequest):
    """Inicia la descarga e instalación automática de Ollama + el modelo ligero elegido."""
    return ollama_setup_manager.start_auto_setup(req.model)

@app.get("/favicon.ico", include_in_schema=False)
async def serve_favicon():
    """Genera un icono .ico en memoria para la ventana de aplicación nativa de Windows."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([(2, 2), (30, 30)], radius=7, fill=(79, 70, 229, 255))
    draw.rounded_rectangle([(7, 11), (25, 23)], radius=3, fill=(255, 255, 255, 240))
    buf = io.BytesIO()
    img.save(buf, format="ICO")
    return Response(content=buf.getvalue(), media_type="image/x-icon")

# Montar frontend para servir la aplicación web en http://localhost:8000
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
