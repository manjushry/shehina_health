# CHANGELOG Shekina

## [1.2.0] - 2025-09-18
- DSL `shekina.for_each` ampliada: periodos (lista/rango) y iteración por tabla con filtros (`==`, `in`, `index in`, `||`).
- Paralelismo real con hilos e instancias hijas aisladas.
- Scheduler por olas (Kahn) cuando existe columna `depends_on` en la tabla iterada.
- Nuevas flags: `strict_dependencies` (falla en ciclos) y `allow_external_deps` (controla dependencias externas).

## [1.0.0] - 2025-09-15
- Clase base Shekina creada como orquestador principal entre KNIME y Python/DB.
