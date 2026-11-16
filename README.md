# 🗂️ TidyDesk AI — Organizador Inteligente de Escritorio y Descargas

> Sistema inteligente y seguro con interfaz gráfica web para clasificar, ordenar y renombrar archivos en Windows mediante Inteligencia Artificial (Ollama local o Gemini API), con modo simulación (*Dry-Run*) y reversión instantánea (*Rollback*).

---

## ✨ Características Principales

1. **Seguridad Absoluta (Zero-Risk):**
   - **Lista negra inmutable:** Nunca toca accesos directos (`.lnk`), enlaces web (`.url`), archivos del sistema (`desktop.ini`), ni archivos ocultos.
   - **Modo Dry-Run visual:** Ves exactamente qué sugiere la IA, qué carpetas creará y cómo renombrará los archivos antes de mover nada.
   - **Historial & Rollback (Undo):** Todas las operaciones generan un ID de transacción; con un clic en "Deshacer Lote", los archivos vuelven exactamente a donde estaban.
2. **Motor de IA Dual + Reglas:**
   - **🦙 Ollama Local:** 100% offline, privado y gratuito (llama3, mistral, phi3, etc.).
   - **✨ Google Gemini API:** Modelos multimodales rápidos en la nube.
   - **⚡ Reglas Heurísticas:** Clasificador inteligente instantáneo que funciona incluso si no hay conexión a internet ni modelos descargados.
3. **Interfaz Gráfica Moderna:**
   - Panel web responsive en modo oscuro (`TailwindCSS`).
   - Selector rápido para **Escritorio** y **Descargas**.
   - Tabla interactiva para editar carpetas propuestas o desmarcar archivos.
   - Pestaña de historial con visualización de transacciones activas y revertidas.

---

## 🚀 Inicio Rápido

### 1. Iniciar con el archivo ejecutable por lotes:
Haz doble clic sobre `iniciar_tidydesk.bat` o corre en terminal:

```bash
python backend/run.py
```

### 2. Abrir en el navegador:
* **Aplicación Web:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Documentación de la API (Swagger / OpenAPI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🗺️ Roadmap de Versiones y Changelog

Puedes consultar el detalle completo de cada versión en **[CHANGELOG.md](CHANGELOG.md)**.

* **[v1.0.0]** ✅ Lanzamiento base con IA Dual, Modo Accesos Directos, Dry-Run y Rollback.
* **[v1.1.0]** ✅ Reglas Personalizadas y Carpetas Externas configurables.
* **[v1.2.0]** ✅ Detector de duplicados por hash SHA-256 y limpiador de instaladores viejos.
* **[v1.3.0]** ✅ Renombrado inteligente con IA multimodal (visión en imágenes y lectura de PDFs).
* **[v1.4.0]** ✅ Modo Guardián en segundo plano (Watchdog) con notificaciones nativas de Windows.
* **[v2.0.0]** ⏳ App nativa empaquetada en `.exe` con icono en la bandeja del sistema (System Tray).

---

## 🏛️ Estructura del Proyecto

```
├── backend/
│   ├── app/
│   │   ├── main.py              # API REST FastAPI y montado de frontend
│   │   ├── config.py            # Rutas de sistema Windows y listas negras
│   │   ├── core/
│   │   │   ├── scanner.py       # Auditoría segura de archivos
│   │   │   ├── cleaner.py       # Detección SHA-256 y limpieza segura
│   │   │   ├── multimodal.py    # Renombrado inteligente con visión y lectura PDF
│   │   │   ├── guardian.py      # Demonio Watchdog en tiempo real y notificaciones
│   │   │   ├── organizer.py     # Movimiento atómico y resolución de colisiones
│   │   │   └── history.py       # Bitácora de transacciones para rollback
│   │   ├── ai/
│   │   │   ├── base.py          # Clase abstracta AIProvider
│   │   │   ├── ollama_provider.py # Conexión a Ollama local
│   │   │   ├── gemini_provider.py # Conexión a Gemini API
│   │   │   └── rules_provider.py  # Clasificador heurístico de respaldo
│   │   └── schemas/             # Modelos de datos Pydantic v2
│   ├── run.py                   # Script de inicio del servidor
│   └── test_direct.py           # Suite de pruebas de integración
├── frontend/
│   ├── index.html               # Dashboard visual interactivo
│   └── app.js                   # Lógica reactiva de la interfaz
├── data/
│   └── history.json             # Registro persistente de transacciones
├── docs/contexto/               # Documentación viva de arquitectura y decisiones
└── iniciar_tidydesk.bat         # Launcher rápido para Windows
```
