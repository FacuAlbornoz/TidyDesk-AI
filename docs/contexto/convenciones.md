# Convenciones de Código y Estándares - TidyDesk AI

## 1. Backend (Python 3.12 / FastAPI)
- **Tipado estricto:** Tipos explícitos con `typing` y modelos Pydantic v2 para validación de datos en cada endpoint.
- **Async/Await:** Uso de funciones asíncronas para I/O y llamadas a proveedores de IA (HTTP client con `httpx`).
- **Manejo de Rutas:** Uso exclusivo de `pathlib.Path` para compatibilidad nativa en Windows y prevención de problemas con barras y espacios.
- **Logging:** Registro detallado de escaneos, propuestas de IA y movimientos ejecutados.
- **Control de Excepciones:** Respuestas HTTP claras con códigos de estado semánticos (400, 404, 422, 500) y mensajes orientados a la UX.

## 2. Frontend (Dashboard Web / Tailwind)
- **4 Estados de UI obligatorios:**
  1. `Loading`: Skeletons / Spinners con mensajes de estado ("Analizando archivos...", "Consultando a la IA...").
  2. `Empty`: Ilustración o icono descriptivo cuando la carpeta ya está limpia u organizada.
  3. `Error`: Mensajes comprensibles con botón de reintento en caso de fallo de red o permisos.
  4. `Success`: Notificaciones toast y resumen de archivos ordenados con opción de Deshacer.
- **Accesibilidad:** Contraste adecuado, etiquetas semánticas y feedback táctil/hover.
- **Nomenclatura:** BEM o utilidades semánticas en Tailwind con variables de color para dark/light mode.
