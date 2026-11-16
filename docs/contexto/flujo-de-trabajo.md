# Flujo de Trabajo y Definición de Terminado (DoD)

## Ciclo de Ejecución
1. **Detección:** El usuario selecciona la carpeta objetivo (`Escritorio` o `Descargas`) y el proveedor de IA (`Ollama Local` o `Gemini API`).
2. **Auditoría (Scan):** El backend filtra y retorna la lista de archivos organizables con metadatos (tamaño, fecha de modificación, extensión).
3. **Planificación IA:** El LLM categoriza los ítems y genera una propuesta con nombres legibles y carpetas lógicas.
4. **Validación Interactiva:** La UI presenta la tabla comparativa con casillas de verificación. El usuario tiene la última palabra.
5. **Ejecución y Persistencia:** Se crea el lote en el sistema de archivos y se guarda el estado en `data/history.json`.
6. **Manejo de Rollback:** En cualquier momento el usuario puede acceder a la pestaña de "Historial" y revertir un lote completo.

## Checklist de Calidad (Definition of Done)
- [ ] Escaneo protegido contra accesos directos de Windows.
- [ ] Conexión dual funcional con switch entre Ollama y Gemini.
- [ ] Fallback elegante si Ollama está apagado o sin conexión.
- [ ] Cero pérdidas o sobrescrituras involuntarias de datos.
- [ ] Los 4 estados de la UI (Loading, Empty, Error, Success) verificados.
