---
title: Mirror · UC2 · KNIME
---

## test_id
Mirror/UC2

## Objetivo
Ejecutar un UPSERT masivo a una tabla SQL desde un DataFrame con `upsert_dataframe`.

## Diagrama de flujo (KNIME)
```mermaid
flowchart LR
  A["Config de conexión"] --> B["File Reader (df)"]
  B --> C["Python Script (Mirror)"]
  C --> D["upsert_dataframe(df, tabla, conflict_cols)"]
  D --> E["Resultado filas afectadas"]
```

## Resultado esperado
- La operación completa sin errores y reporta filas afectadas (> 0 cuando aplica).
