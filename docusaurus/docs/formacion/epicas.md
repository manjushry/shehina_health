# Épicas para desarrollo incremental

Esta sección describe las épicas del proyecto Shekina para probar y validar las clases principales de forma incremental. Cada épica corresponde a una fase de desarrollo y validación progresiva.


## Épica 1: Base y configuración ✅

**Prompt:**
"Como desarrollador del framework Shekina, necesito crear y validar la clase base `Aleya` para gestionar contextos, configuraciones y datos tabulares de forma genérica. Debo asegurar que los métodos principales (`set_config`, `get_config`, `set_data`, `get_data`, `set_context`, `get_context`) funcionen correctamente y estén alineados con el código original. Además, debo documentar los atributos, métodos y ejemplos de uso en la wiki, changelog y README."


## Épica 2: Conexión y persistencia

**Prompt:**
"Como desarrollador del framework Shekina, necesito implementar y validar la clase `BereshitSQL` para gestionar la conexión, ejecución de scripts SQL y manejo de contexto de datos/tablas en bases de datos (inicialmente PostgreSQL). Debo asegurar que los métodos principales (`connect`, `execute_sql`, `fetch_dataframe`, `bootstrap`) funcionen correctamente, que los scripts SQL estén centralizados y que la documentación refleje el flujo de inicialización y despliegue. Además, debo preparar ejemplos de uso y pruebas unitarias para validar la persistencia y la automatización del entorno."

## Épica 3: Orquestación y lógica avanzada
- Implementar `AlchemistPrime` y `Shekina` para orquestación de procesos.
- Validar la interacción entre módulos.
- Documentar flujos de trabajo y pruebas avanzadas.

## Épica 4: Grafo y relaciones
- Implementar y probar la clase `DaathGraph`.
- Validar la integración con `Aleya`.
- Documentar ejemplos de uso y relaciones.

---

Cada épica incluirá pruebas unitarias, ejemplos y documentación detallada en la wiki.