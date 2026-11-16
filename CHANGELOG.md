# 📜 Historial de Cambios (Changelog) — TidyDesk AI

Todas las notas de las versiones y evoluciones del proyecto se documentan en este archivo.

---

## [v2.2.0] - 2026-11-16
### 🏆 Edición Pro Studio: Escáner de Hardware, Gestor de Modelos & Rediseño Visual
- **Rediseño Integral "Pro Studio UI":** Interfaz de escritorio oscura con efectos *glassmorphism*, iluminación radial ambiental, tipografía técnica (`Inter` + `JetBrains Mono`), iconografía vectorial SVG y corrección total de alineación sin desbordes.
- **Logo e Icono Oficial HD en Barra de Tareas de Windows 11:**
  - Generador vectorial de alta definición (`create_pro_brand_icon`) en resoluciones 512x512, 192x192 y `.ico` multi-capa.
  - Integración de `Web App Manifest` (`/manifest.json`), `AppUserModelID` de Windows y perfil dedicado de ventana para mostrar el logo oficial en la barra de tareas y barra de título de Windows 11.
- **Escáner de Especificaciones de la PC en Vivo (`Win32` + `CIM`):**
  - Detección automática de **CPU** (modelo y núcleos/hilos), **Memoria RAM** (total y disponible en tiempo real), **Placa de Video / GPU** (modelo dedicado o integrado + VRAM) y **Disco Libre**.
  - Recomendador inteligente que etiqueta con `🏆 IDEAL PARA TU PC` el modelo de IA óptimo según la RAM y VRAM reales del equipo.
- **Gestor Visual de Modelos Instalados en la PC:**
  - Muestra claramente qué modelos de Ollama ya están instalados en el disco (`✅ YA INSTALADO`) junto con su peso en GB, permite activarlos con 1 clic o desinstalarlos (`×`) para liberar espacio.
- **Barra Visual de Distribución de Almacenamiento:** Gráfico segmentado multicolor que desglosa cuánto espacio ocupan *Videos, Instaladores, Documentos, Imágenes y Modelos 3D* en la carpeta analizada.
- **Compresor Cold Storage (`.ZIP`):** Nueva opción en el Limpiador para empaquetar archivos seleccionados en un backup `.zip` comprimido antes de archivarlos.
- **Exportar / Importar Reglas (`.json`) y Buscador en Vivo:** Portabilidad de reglas entre distintas computadoras y filtro instantáneo en las pestañas de Reglas e Historial.
- **Switch "Iniciar junto con Windows":** Opción integrada en la barra superior para registrar/quitar TidyDesk AI del arranque automático de Windows (`HKCU\...\Run`).

---

## [v2.1.0] - 2026-11-16
### 🪟 Edición Escritorio Nativo, Selector Visual de Carpetas & Auto-Instalador Ollama
- **Ventana de Aplicación Nativa (Sin barras de navegador):** Al abrir el `.exe` o desde el icono de la bandeja del sistema, la interfaz se lanza como una ventana independiente de escritorio (`--app`) con su propio icono `.ico` y barra de título de Windows, sin barra de direcciones ni pestañas.
- **Selector Visual de Carpetas de Windows (`📂 Examinar...`):**
  - En el **Paso 1 (Seleccionar Carpeta)**: Nueva tarjeta `📂 Otra Carpeta de tu PC...` que abre el diálogo nativo del Explorador de Windows (`TopMost`) para auditar, organizar o limpiar cualquier carpeta o disco.
  - En **Reglas Personalizadas**: Botón `📂 Examinar...` junto al campo de destino para elegir la carpeta con un clic sin escribir rutas a mano.
  - En **Modo Guardián**: Posibilidad de vigilar cualquier carpeta personalizada de la PC.
- **Auto-Instalador de Ollama y Descarga de Modelos en 1 Clic (`system_utils.py`):**
  - Despierta automáticamente el servicio local de Ollama (`ollama serve`) si está instalado pero apagado.
  - Si se ejecuta en una PC que no tiene Ollama, descarga `OllamaSetup.exe`, lo instala silenciosamente y descarga el modelo ligero elegido (`llama3.2:1b`, `llama3.2:3b` o `llama3`) mostrando una barra de progreso en tiempo real y el espacio libre en disco.
- **Actualización Sin Desinstalar:** El ejecutable `dist/TidyDesk_AI.exe` actualiza solo el binario conservando intacta la carpeta `data/` con las reglas y el historial del usuario.

---

## [v2.0.0] - 2026-11-16
### 🖥️ Aplicación de Escritorio Nativa (.exe & System Tray)
- **Controlador de Bandeja del Sistema (`backend/tray_app.py`):** Integración nativa con la bandeja del sistema de Windows (al lado del reloj) mediante `pystray`.
- **Iconografía Dinámica de Estado:** Generación vectorial de icono con indicador luminoso que cambia a verde esmeralda cuando el **Modo Guardián** está activo.
- **Menú Contextual Rápido (Clic Derecho en Tray):**
  - `🗂️ Abrir Panel TidyDesk AI` (también al hacer doble clic en el icono).
  - `🛡️ Modo Guardián (Tiempo Real)` (activar/pausar directamente sin abrir el navegador).
  - `📥 Abrir Carpeta Descargas` y `🖥️ Abrir Carpeta Escritorio`.
  - `❌ Salir de TidyDesk AI` (apagado limpio del servidor y del demonio Watchdog).
- **Ejecución Silenciosa Sin Consola (`iniciar_tidydesk_tray.vbs`):** Lanzador nativo de Windows que ejecuta TidyDesk AI en segundo plano sin dejar ninguna ventana negra de terminal abierta.
- **Compilador One-Click a `.exe` (`compilar_exe.bat`):** Script automatizado con `PyInstaller` (`--onefile --noconsole`) y soporte híbrido de rutas (`sys._MEIPASS`) en `config.py` para distribuir un único archivo `TidyDesk_AI.exe` 100% portable.

---

## [v1.4.0] - 2026-11-16
### 🛡️ Modo Guardián en Segundo Plano (Watchdog Daemon)
- **Servicio Watchdog en Tiempo Real:** Monitoreo continuo y no bloqueante de la carpeta de **Descargas** o **Escritorio** mediante hilos demonios con `watchdog`.
- **Protección contra Descargas en Curso:** Ignora automáticamente archivos temporales de navegadores (`.crdownload`, `.part`, `.tmp`, `.opdownload`) y verifica la estabilización de bytes y desbloqueo de lectura antes de intervenir.
- **2 Niveles de Automatización:**
  - *Clasificación Completa:* Organiza cualquier archivo nuevo combinando Reglas Personalizadas y heurística inteligente.
  - *Solo Reglas Personalizadas ⭐:* Mueve únicamente los archivos que coincidan con las reglas creadas por el usuario.
- **Renombrado Multimodal en Vivo:** Renombra al vuelo facturas PDF e imágenes genéricas apenas terminan de descargarse.
- **Notificaciones Nativas de Windows:** Avisos en la bandeja del sistema de Windows informando qué archivo fue organizado y hacia qué carpeta.
- **Feed en Tiempo Real con Rollback Instantáneo:** Nueva pestaña `🛡️ Guardián` con bitácora en vivo y botón `↩️ Deshacer` directo en cada evento.

---

## [v1.3.0] - 2026-11-16
### ✨ Renombrado con IA Multimodal (Visión & Extracción de PDFs)
- **Extracción de Contenido de PDFs:** Integración de `pypdf` para extraer de forma segura y liviana el texto plano de la primera página de documentos PDF genéricos (`download (1).pdf`, `documento.pdf`).
- **Detección Heurística e IA de Entidades:** Reconocimiento de tipos de comprobante (`Factura`, `Comprobante`, `Recibo`, `Constancia`, `TP`), entidades emisoras (`EPEC`, `Telecom`, `Mercado Pago`, `AFIP`, `Universidad`) y períodos (`Noviembre_2026`, fechas ISO).
- **Visión Multimodal para Imágenes:** Integración con Gemini Vision y miniaturas optimizadas (`PIL`) para describir capturas y fotos genéricas (`Screenshot (1).png` -> `Captura_...` o descripción semántica de la pantalla).
- **Columna de 'Nuevo Nombre' Editable en Dry-Run:** Nueva columna en la tabla de vista previa con inputs interactivos para revisar o personalizar el nuevo nombre antes de confirmar el movimiento.
- **Badges Visuales de Renombrado:** Indicadores destacados `✨ Renombrado por IA` para que el usuario identifique al instante qué archivos tienen sugerencia de nuevo nombre.
- **Interruptor de Control en Panel:** Switch interactivo en el Paso 1 para activar o desactivar el renombrado multimodal a demanda.
- **Preservación Segura de Extensiones & Rollback:** Sanitización para evitar pérdida accidental de extensiones y compatibilidad total con el historial de reversión atómica de 1 clic.
- **Archivo `requirements.txt`:** Definición estandarizada de dependencias (`fastapi`, `uvicorn`, `pydantic`, `httpx`, `pillow`, `pypdf`, `watchdog`, `pystray`) para máxima portabilidad entre computadoras.

---

## [v1.2.0] - 2026-11-16
### 🧹 Detector de Duplicados (SHA-256) & Limpiador Inteligente
- **Pestaña 'Limpiador' en UI:** Nueva vista integrada para auditar duplicados de almacenamiento e instaladores antiguos.
- **Fingerprint Criptográfico SHA-256:** Detección de duplicados exactos mediante hash SHA-256, optimizado previamente agrupando por tamaño de bytes para evitar lecturas innecesarias en disco.
- **Identificación Inteligente de Original vs. Duplicado:** Distingue el archivo original (nombre más canónico/corto) de sus copias redundantes (ej: `archivo (1).pdf` o `archivo - copia.pdf`).
- **Detección de Instaladores Antiguos:** Identifica instaladores pesados (`.exe`, `.msi`) descargados hace más de 30 días que consumen almacenamiento residual.
- **Limpieza Segura con Rollback:** Los archivos seleccionados no se eliminan permanentemente; se trasladan a una carpeta de cuarentena segura `_Limpieza_TidyDesk` y generan un registro de transacción con Rollback atómico de 1 clic.
- **Métricas de Espacio Recuperable:** Tarjetas visuales de cálculo instantáneo de MB/GB desperdiciados y espacio total recuperable.

---

## [v1.1.0] - 2026-11-16
### ⭐ Reglas de Destino Personalizadas & Carpetas Externas
- **Pestaña de Reglas en UI:** Nueva pestaña dedicada en la barra superior para gestionar reglas con estados activa/pausada y eliminación.
- **Carpetas Externas Absolutas:** Capacidad de enviar archivos a cualquier disco o carpeta del sistema (ej: `D:\Proyectos\Impresion_3D` o `C:\Mis_Estudios`).
- **Prioridad Máxima del Usuario:** Las reglas definidas por el usuario tienen precedencia absoluta sobre la IA y sobre reglas generales.
- **Soporte de Extensiones y Palabras Clave:** Filtros por múltiples extensiones (`.stl, .step, .gcode, .3mf`) o palabras clave (`parcial, tp, seminario, factura`).
- **Persistencia en `data/rules.json`:** Guardado seguro, dinámico y editable de las directivas del usuario (excluido de Git para portabilidad).
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
