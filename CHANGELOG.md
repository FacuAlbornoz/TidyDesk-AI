# 📜 Historial de Cambios (Changelog) — TidyDesk AI

Todas las notas de las versiones y evoluciones del proyecto se documentan en este archivo.

---

## [v1.1.0] - 2026-11-16
### ⭐ Reglas de Destino Personalizadas & Carpetas Externas
- **Pestaña de Reglas en UI:** Nueva pestaña dedicada en la barra superior para gestionar reglas con estados activa/pausada y eliminación.
- **Carpetas Externas Absolutas:** Capacidad de enviar archivos a cualquier disco o carpeta del sistema (ej: `D:\Facu\Impresora 3d` o `D:\Facu\Itec`).
- **Prioridad Máxima del Usuario:** Las reglas definidas por el usuario tienen precedencia absoluta sobre la IA y sobre reglas generales.
- **Soporte de Extensiones y Palabras Clave:** Filtros por múltiples extensiones (`.stl, .step, .gcode, .3mf`) o palabras clave (`parcial, tp, seminario, itec`).
- **Persistencia en `data/rules.json`:** Guardado seguro, dinámico y editable de las directivas del usuario.
- **Visualización en Dry-Run:** Badges dorados `⭐ Regla Personalizada` y rutas de destino completas en la tabla interactiva de vista previa.

---

## [v1.0.0] - 2026-11-16
### ✨ Lanzamiento Inicial
- **Backend FastAPI:** Servidor REST con endpoints `/api/health`, `/api/scan`, `/api/plan`, `/api/execute`, `/api/history` y `/api/rollback`.
- **Motor de IA Dual:** Integración con **Ollama Local** (100% offline y privado) y **Google Gemini API**, con fallback a reglas heurísticas instantáneas.
- **Seguridad Windows NTFS:** Sanitización estricta de rutas de carpetas y nombres de archivo para prevenir errores de caracteres ilegales o espacios terminales (`[WinError 123]`).
- **Organizador de Accesos Directos (.lnk / .url):** Modo para agrupar iconos del Escritorio en carpetas temáticas (`🎮 Juegos`, `💻 Desarrollo & Programación`, `🎨 Diseño & Creatividad`, `🌐 Navegadores Web`, `🎧 Multimedia & Comunicación`, `📋 Productividad & Oficina`).
- **Dry-Run & Rollback:** Vista previa interactiva con confirmación previa y registro de transacciones atómicas para deshacer cualquier movimiento con un solo clic.
- **Dashboard Web:** Interfaz moderna en modo oscuro construida con TailwindCSS y los 4 estados de UI (Loading, Empty, Error, Success).
- **Lanzador para Windows:** Archivo `iniciar_tidydesk.bat` listo para doble clic.

---

## 🗺️ Roadmap de Próximas Versiones

- **[v1.2.0] Detector de Duplicados & Limpiador Inteligente:**
  - Comparación de hashes SHA-256 para detectar descargas repetidas (`archivo (1).pdf`).
  - Detección de instaladores antiguos (`.exe`/`.msi`) para sugerir recuperación de espacio.

- **[v1.3.0] Renombrado con IA Multimodal (Visión & Contenido):**
  - Análisis de imágenes con IA para renombrar capturas (`Screenshot (1).png` $\rightarrow$ `Diagrama_Arquitectura.png`).
  - Lectura de texto en PDFs para extraer títulos y fechas de facturas o comprobantes.

- **[v1.4.0] Modo Guardián en Segundo Plano (Watchdog Daemon):**
  - Monitoreo en tiempo real de Descargas con la librería `watchdog`.
  - Notificaciones nativas en Windows con botón de deshacer rápido.

- **[v2.0.0] Aplicación de Escritorio Nativa (.exe & System Tray):**
  - Empaquetado ejecutable sin necesidad de abrir terminal.
  - Icono en la barra de tareas al lado del reloj.
