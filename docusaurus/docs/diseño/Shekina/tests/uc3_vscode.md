---
title: Shekina · UC3 · VS Code
---

## test_id
Shekina/UC3

## Objetivo
Verificar que, cuando falta el DataFrame para un `process_key` válido, se registra un warning y el flujo continúa sin error.

## Ejecución (pytest)
```
pytest -q tests\Shekina\test_shekina_uc3.py::test_missing_dataframe_logs_warning
```

## Diagrama de flujo
```mermaid
flowchart LR
  A["config_df (execute=true)"] --> B{"existe df?"}
  B -- "No" --> X["Log warning y continuar"]
  B -- "Sí" --> C["Continuar flujo UC1"]
```
