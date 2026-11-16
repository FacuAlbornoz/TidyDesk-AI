# Arquitectura del Sistema - TidyDesk AI 🗂️🤖

## 1. Stack Tecnológico
- **Backend Core:** Python 3.12+ / FastAPI / Uvicorn / Pydantic v2.
- **Seguridad & File System:** Biblioteca estándar (`pathlib`, `shutil`, `os`, `hashlib`, `json`).
- **Motor de IA Dual:**
  - `OllamaProvider`: Cliente HTTP REST para modelos locales (llama3, mistral, phi3) sin conexión a internet ni costo.
  - `GeminiProvider`: SDK oficial (`google-genai` / REST) para inferencia de alto rendimiento y multimodalidad en la nube.
- **Frontend / Dashboard UI:**
  - Modern Web Dashboard responsivo servido localmente.
  - TailwindCSS (Dark/Light mode nativo, estética moderna con paleta Slate/Indigo/Emerald).
  - Interactividad reactiva, tabla de previsualización (Dry-Run), selección manual de archivos, historial y rollback en 1 clic.

## 2. Mapa de Carpetas y Módulos
```
/ (raíz del proyecto)
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # Entrada FastAPI, middlewares, CORS y endpoints
│   │   ├── config.py              # Rutas de sistema (Desktop, Downloads) y configuraciones
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── scanner.py         # Escaneo del sistema de archivos con lista negra estricta
│   │   │   ├── organizer.py       # Algoritmo de resolución de colisiones y movimiento
│   │   │   └── history.py         # Registro de transacciones atómicas para Undo/Rollback
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Clase abstracta AIProvider
│   │   │   ├── ollama_provider.py # Conexión a Ollama local
│   │   │   └── gemini_provider.py # Conexión a Gemini API
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── scan.py            # Esquemas Pydantic para archivos detectados
│   │       └── organize.py        # Esquemas para planes de organización y rollback
│   ├── requirements.txt           # Dependencias Python
│   └── run.py                     # Script para iniciar backend con 1 comando
├── frontend/                      # Dashboard interactivo para el usuario
│   ├── index.html                 # Vista interactiva SPA moderna
│   └── app.js                     # Controlador de lógica, llamadas a API y estados UI
├── data/                          # Persistencia de transacciones
│   └── history.json               # Bitácora de operaciones para rollback
├── docs/
│   └── contexto/                  # Contexto vivo del sistema
└── GEMINI.md                      # Vinculación del proyecto
```

## 3. Flujo de Datos y Transacciones (DoD)
1. **Escaneo Seguro (`/api/scan`):**
   - El backend escanea el Escritorio o Descargas.
   - Aplica filtros de seguridad (excluye `.lnk`, `.url`, carpetas de sistema, archivos ocultos y bloqueados).
2. **Clasificación Inteligente (`/api/plan`):**
   - El proveedor de IA activo (Ollama o Gemini) evalúa la lista de archivos con sus nombres, extensiones, tamaños y fechas.
   - Genera una propuesta estructurada en formato JSON estricto con carpetas temáticas sugeridas.
3. **Revisión Humana (Dry-Run en UI):**
   - El usuario ve en la interfaz qué se moverá y a dónde.
   - Puede excluir archivos desmarcándolos o cambiar la carpeta destino.
4. **Ejecución y Registro de Transacción (`/api/execute`):**
   - Se crean las carpetas necesarias de forma segura.
   - Se mueven los archivos resolviendo posibles colisiones (sufijos `_1`, etc.).
   - Se guarda un `transaction_id` con el estado original exacto en `data/history.json`.
5. **Reversión Instantánea (`/api/rollback`):**
   - Con presionar "Deshacer", el backend lee la transacción y devuelve cada archivo a su ruta previa original.

## 4. Guardas y Límites Estrictos
- ❌ **JAMÁS** borrar archivos físicamente (únicamente mover a carpetas organizadas).
- ❌ **JAMÁS** mover accesos directos (`.lnk`) de programas del usuario.
- ❌ **JAMÁS** operar sin confirmación explícita previa del usuario (Dry-Run obligatorio).
