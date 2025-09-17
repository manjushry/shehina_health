# Wishlist y Seguimiento de Tareas

## Tareas actuales
- [ ] Definir estructura de carpetas y módulos
- [ ] Configurar entorno reproducible
- [ ] Crear documentación interactiva
- [ ] Implementar clases base y especializadas
- [ ] Integrar control de versiones y ramas
- [ ] Crear pruebas unitarias

## Ideas futuras
- [ ] Integración CI/CD
- [ ] Ejemplos avanzados de uso
- [ ] Plugins para nuevos backends
- [ ] Dashboard de monitoreo
- [ ] Integrar funcionalidades de aprendizaje automático en Daath (ML, agentes inteligentes tipo Raziel, búsqueda de modelos entrenados en medicina y acceso a bases de conocimiento en línea)

# Wishlist de Mejoras y Recomendaciones

## AlchemistPrime
- **Permitir configuración de paralelismo en Polars para aprovechar CPUs multinúcleo.**
  - Nota: Polars ya gestiona el paralelismo por defecto, pero se puede documentar cómo ajustar el número de threads si se requiere tuning avanzado.
- **Manejo robusto para leer archivos xlsx, xls (xml), csv, tanto recibiendo un folder como un archivo en particular.**
  - Implementar funciones que automaticen la carga y normalización de datos desde múltiples fuentes y formatos, similar a Polars pero también integrando el backend de PostgreSQL para normalización y homologación.
- **Backend PostgreSQL:** Incluir funciones para normalizar, homologar, limpiar y transformar datos directamente en la base de datos, permitiendo workflows avanzados y eficientes.
  - Documentar cómo estas funciones pueden ser usadas desde el pipeline y cómo se integran con el ecosistema Python.

## DaathGraph
- **Optimizar el uso de memoria para grafos muy grandes, gestionando el grafo nativamente en PostgreSQL usando la extensión AGE.**
  - El grafo se activa en memoria solo para relaciones específicas (ej: ES_SINONIMO_DE), mientras que otras (ej: PERTENECE_A) se consultan directamente en PostgreSQL.
- **Documentar la arquitectura híbrida:** DaathGraph primero consulta a PostgreSQL y solo activa el grafo en memoria para casos de análisis avanzado.
- **Incluir en la documentación la integración con AGE y la gestión nativa del grafo en PostgreSQL como primera implementación.**

## BereshitSQL
- Añadir soporte para más motores SQL usando SQLAlchemy (ej: SQLite, Oracle).
- Implementar pool de conexiones reutilizable para procesos batch.
- Métodos para validación de esquemas y migraciones automáticas.
- Gestión de errores con códigos y mensajes personalizados.

## Mirror
- Soporte para operaciones asíncronas usando async SQLAlchemy.
- Validaciones automáticas de integridad antes de upserts/updates.
- Métricas de rendimiento y profiling de operaciones.
- Configuración avanzada de transacciones (aislamiento, retries).

## Shekina
- **Permitir orquestación desde otros sistemas de automatización además de KNIME (ej: Airflow, Prefect, scripts declarativos).**
  - Las funciones de Shekina pueden recibir declaraciones por tablas y diccionarios, lo que permite desacoplar el backend de automatización.
- Documentar ejemplos de integración y orquestación multiplataforma.

## General
- Añadir diagramas UML y de flujo en la documentación para cada clase y proceso.
- Incluir ejemplos de uso real (end-to-end) en README y docstrings.
- Documentar casos de error y mejores prácticas de manejo de excepciones.
- Añadir tests unitarios y de integración para cada módulo.
- Usar type hints en todos los métodos públicos.
