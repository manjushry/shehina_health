---
title: BereshitSQL · UC2 · KNIME
---

## test_id
BereshitSQL/UC2

## Objetivo
Leer datos con `fetch_dataframe(query)` desde KNIME y devolver un DataFrame.

## Diagrama de flujo (KNIME)
```mermaid
flowchart LR
  A["Config de conexión"] --> B["Python Script (BereshitSQL)"]
  B --> C["connect(); df = fetch_dataframe(SQL)"]
  C --> D["Interactive Table"]
```

## Resultado esperado
- Se obtiene un DataFrame con filas y columnas esperadas.
