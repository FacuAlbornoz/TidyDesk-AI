# Glosario del Dominio - TidyDesk AI

- **Dry-Run (Modo Simulación):** Proceso en el cual la IA propone la categorización y renombrado de los archivos, visualizándose en la interfaz gráfica sin alterar el sistema de archivos real.
- **Rollback (Deshacer):** Operación inversa que lee el historial de una transacción y devuelve todos los archivos movidos a sus rutas y nombres originales.
- **Transaction ID:** Identificador único (UUID) que agrupa un lote de archivos movidos simultáneamente en una sola operación de organización.
- **Lista Negra / Guardrails:** Regla estricta que excluye del análisis archivos sensibles del sistema operativo Windows (`.lnk`, `.url`, `.ini`, `.sys`, carpetas ocultas).
- **AIProvider:** Interfaz abstracta que unifica la forma en que el backend consulta a diferentes modelos de lenguaje (Ollama o Gemini), garantizando desacoplamiento.
- **Colisión de Nombres:** Situación en la cual el destino propuesto ya contiene un archivo con el mismo nombre; se resuelve automáticamente añadiendo un sufijo numérico (`archivo_1.ext`).
