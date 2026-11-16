# Errores Conocidos y Mitigaciones - TidyDesk AI

| Incidencia Potencial | Causa Raíz | Mitigación Implementada |
| :--- | :--- | :--- |
| `PermissionError: [WinError 32]` | El archivo está abierto por otra aplicación (ej: Word, PDF reader o instalador corriendo). | El backend detecta archivos bloqueados durante el escaneo y los omite con un aviso sin interrumpir el resto. |
| `Ollama Connection Refused` | El servicio Ollama en Windows no está iniciado en `http://localhost:11434`. | Endpoint de verificación de salud (`/api/health`) que notifica en la UI para sugerir iniciar Ollama o conmutar a Gemini. |
| Caracteres especiales en rutas | Rutas con tildes, espacios o símbolos de Windows. | Uso de `pathlib.Path` nativo y resolución absoluta de rutas. |
| Timeout de IA | Consultas con cientos de archivos superan el tiempo de espera. | Procesamiento por lotes (batches de 20-30 archivos) y prompts concisos en formato JSON. |
