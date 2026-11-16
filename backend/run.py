import uvicorn
import os
import sys
import asyncio
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Añadir directorio backend al sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando TidyDesk AI Server...")
    print("📍 URL de la Aplicación: http://127.0.0.1:8000")
    print("📖 Documentación OpenAPI: http://127.0.0.1:8000/docs")
    print("=" * 60)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
