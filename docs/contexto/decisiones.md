# Registro de Decisiones de Arquitectura (ADR)

> ⚠️ **Control de Guardas:** Ante cualquier cambio estructural (arquitectura, cambio de framework, borrado o agregado de librerías), el agente **DEBE solicitar confirmación explícita antes de ejecutarlo** y luego registrarlo cronológicamente en este documento.

---

### [ADR-001] · [2026-09-01 23:37] - Activación del Sistema Operativo de Reglas Antigravity
- **Contexto:** Establecimiento de la metodología Senior Product Engineer y Definition of Done para el proyecto.
- **Decisión:** Crear e integrar .agents/rules/antigravity_global_rules.md con trigger always_on.
- **Consecuencias:** Reglas activas para todas las sesiones.

---

### [ADR-002] a [ADR-006] · [2026-09-01 a 2026-09-02] - Festival Cultural Río Cuarto 2026 (Completado y Archivado)
- Histórico de la práctica web inicial.

---

### [ADR-007] · [2026-11-16 00:30] - Implementación de TidyDesk AI (Seminario AI)
- **Contexto:** El usuario requiere una solución integral, segura y estética para organizar automáticamente el Escritorio y Descargas mediante Inteligencia Artificial, con control visual y capacidad de deshacer cambios.
- **Decisión:** 
  1. Construir un backend en **Python 3.12 con FastAPI** para gestión segura de archivos del sistema operativo.
  2. Implementar una capa abstracta de IA **Dual Provider (`Ollama` local + `Gemini API` en la nube)** conmutables desde la UI.
  3. Establecer un protocolo estricto de **Dry-Run visual** obligatorio antes de cualquier operación de movimiento.
  4. Desarrollar un sistema de **Rollback atómico** respaldado en bitácora de transacciones (`history.json`).
  5. Excluir de forma irrestricta accesos directos (`.lnk`, `.url`), archivos ocultos y del sistema.
  6. Diseñar un **Dashboard interactivo moderno** con soporte para modo oscuro/claro y visualización de los 4 estados UI (Loading, Empty, Error, Success).
- **Consecuencias:** Seguridad absoluta para los archivos del usuario, privacidad opcional con modelos locales y UX intuitiva.
