# 🗂️ TidyDesk AI (v2.0) — Organizador Inteligente de Escritorio y Descargas

> Aplicación nativa y segura para Windows con interfaz gráfica moderna, icono en la bandeja del sistema (*System Tray*) y Modo Guardián en tiempo real para clasificar, limpiar duplicados y renombrar archivos mediante Inteligencia Artificial (Ollama local o Gemini API), con simulación previa (*Dry-Run*) y reversión atómica (*Rollback*).

---

## ✨ Características Principales

1. **Seguridad Absoluta (Zero-Risk):**
   - **Lista negra inmutable:** Protege archivos críticos del sistema (`desktop.ini`, `.sys`, `.dll`, ocultos) y permite organizar accesos directos (`.lnk` / `.url`) de forma opcional y controlada.
   - **Modo Dry-Run interactivo:** Previsualizá y editá tanto la carpeta destino como el nuevo nombre antes de mover un solo archivo.
   - **Historial & Rollback (Undo):** Cada operación queda registrada con un ID único; con un clic en "Deshacer", los archivos regresan a su ruta y nombre originales.
2. **Motor de IA Dual + Reglas Personalizadas:**
   - **⭐ Reglas Personalizadas (Prioridad #1):** Creá tus propias directivas por extensión o palabra clave hacia cualquier carpeta o disco externo.
   - **🦙 Ollama Local:** 100% offline, privado y gratuito (`llama3`, `mistral`, `phi3`, etc.).
   - **✨ Google Gemini API:** Clasificación y visión multimodal ultrarrápida en la nube.
   - **⚡ Reglas Heurísticas:** Clasificador instantáneo sin conexión.
3. **Renombrado Multimodal (Visión & PDFs):**
   - Extrae títulos, entidades y períodos de la primera página de PDFs (`download (1).pdf` → `Factura_EPEC_Noviembre_2026.pdf`) y normaliza capturas de pantalla e imágenes genéricas.
4. **Limpiador Inteligente (SHA-256):**
   - Detecta archivos duplicados idénticos bit a bit mediante hash criptográfico SHA-256 e instaladores antiguos (`>30 días`) con archivo seguro y rollback.
5. **Modo Guardián en Tiempo Real (`Watchdog`) & System Tray:**
   - Vigila tu carpeta de Descargas en segundo plano (esperando a que finalicen los `.crdownload`/`.part`) y vive en la bandeja del sistema junto al reloj de Windows sin requerir una consola abierta.

---

## 🚀 Inicio Rápido

### 1. Instalar dependencias (primera vez o en otra PC):
```bash
pip install -r requirements.txt
```

### 2. Formas de ejecución en Windows:
* **Modo Bandeja del Sistema (Sin ventana de consola - Recomendado):**
  Haz doble clic sobre `iniciar_tidydesk_tray.vbs` (inicia el icono junto al reloj de Windows y abre el panel web).
* **Modo Consola Tradicional:**
  Haz doble clic sobre `iniciar_tidydesk.bat` o ejecuta `python backend/run.py`.
* **Compilar a Ejecutable Portable (`dist/TidyDesk_AI.exe`):**
  Haz doble clic sobre `compilar_exe.bat`.

### 3. Acceso al Panel Web:
* **Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Documentación API (Swagger / OpenAPI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🗺️ Roadmap de Versiones Completado

Puedes consultar el detalle técnico de cada versión en **[CHANGELOG.md](CHANGELOG.md)**.

* **[v1.0.0]** ✅ Lanzamiento base con IA Dual, Modo Accesos Directos, Dry-Run y Rollback.
* **[v1.1.0]** ✅ Reglas Personalizadas y Carpetas Externas configurables.
* **[v1.2.0]** ✅ Detector de duplicados por hash SHA-256 y limpiador de instaladores viejos.
* **[v1.3.0]** ✅ Renombrado inteligente con IA multimodal (visión en imágenes y lectura de PDFs).
* **[v1.4.0]** ✅ Modo Guardián en segundo plano (Watchdog) con notificaciones nativas de Windows.
* **[v2.0.0]** ✅ App de escritorio con icono en la bandeja del sistema (System Tray), lanzador silencioso y compilador `.exe`.
* **[v2.1.0]** ✅ Ventana nativa de escritorio (`--app`), selector visual de carpetas de Windows (`📂 Examinar...`) y auto-instalador de Ollama + modelos en 1 clic.
* **[v2.2.0]** ✅ Edición **Pro Studio**: Rediseño visual, logo HD en barra de tareas Windows 11, escáner de hardware (CPU/RAM/GPU), gestor de modelos instalados, barra de almacenamiento, compresor `.ZIP`, exportar/importar reglas e inicio con Windows.

---

## 🏛️ Estructura del Proyecto

```
├── backend/
│   ├── app/
│   │   ├── main.py                # API REST FastAPI y montado de frontend
│   │   ├── config.py              # Rutas portables Windows/PyInstaller y listas negras
│   │   ├── core/
│   │   │   ├── scanner.py         # Auditoría segura de archivos
│   │   │   ├── cleaner.py         # Detección SHA-256 y limpieza segura
│   │   │   ├── multimodal.py      # Renombrado inteligente con visión y lectura PDF
│   │   │   ├── guardian.py        # Demonio Watchdog en tiempo real y notificaciones
│   │   │   ├── system_utils.py    # Diálogo nativo de carpetas Windows y Auto-Setup Ollama
│   │   │   ├── rules_manager.py   # Motor de reglas personalizadas del usuario
│   │   │   ├── organizer.py       # Movimiento atómico y resolución de colisiones
│   │   │   └── history.py         # Bitácora de transacciones para rollback
│   │   ├── ai/
│   │   │   ├── base.py            # Clase abstracta AIProvider
│   │   │   ├── ollama_provider.py # Conexión a Ollama local
│   │   │   ├── gemini_provider.py # Conexión a Gemini API
│   │   │   └── rules_provider.py  # Clasificador heurístico de respaldo
│   │   └── schemas/               # Modelos de datos Pydantic v2
│   ├── run.py                     # Script de inicio del servidor en consola
│   └── tray_app.py                # Aplicación nativa de Bandeja del Sistema (System Tray)
├── frontend/
│   ├── index.html                 # Dashboard visual interactivo (5 pestañas)
│   └── app.js                     # Controlador reactivo de la interfaz
├── data/                          # Almacenamiento local (ignorado en Git para portabilidad)
├── iniciar_tidydesk.bat           # Launcher en consola para Windows
├── iniciar_tidydesk_tray.vbs      # Launcher silencioso sin consola (System Tray)
├── compilar_exe.bat               # Empaquetador automático a TidyDesk_AI.exe
└── requirements.txt               # Dependencias del proyecto
```
