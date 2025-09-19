---
title: Mirror · UC1 · KNIME
---

## test_id
Mirror/UC1

## Objetivo
Alinear un DataFrame al esquema de una tabla destino usando `prepare_dataframe`.

## Diagrama de flujo (KNIME)
```mermaid
flowchart LR
  A["File Reader (df fuente)"] --> B["Python Script (Mirror)"]
  B --> C["prepare_dataframe(df, tabla)"]
  C --> D["Preview columnas ordenadas"]
```

## Resultado esperado
- El DataFrame devuelto contiene solo las columnas de la tabla, en el orden correcto, con nulos estandarizados.
