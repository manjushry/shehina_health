---
title: BereshitSQL · UC1 · KNIME
---

## test_id
BereshitSQL/UC1

## Objetivo
Ejecutar scripts de bootstrap (activación de extensiones/schemas/funciones) desde KNIME.

## Diagrama de flujo (KNIME)
```mermaid
flowchart LR
  A["Config de conexión"] --> B["Python Script (BereshitSQL)"]
  B --> C["connect() + deploy_functions()"]
  C --> D["Logs y resultado"]
```

## Resultado esperado
- Los scripts configurados se ejecutan sin errores y el `search_path` queda establecido.
