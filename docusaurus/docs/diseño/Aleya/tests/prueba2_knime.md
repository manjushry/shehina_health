---
title: Aleya - Prueba 2 · KNIME (carga de dataset mínimo)
---

## test_id
Aleya/test/prueba2

## Objetivo
Validar la carga de un dataset mínimo (3 filas) en Aleya dentro de un flujo KNIME.

## Inputs
- `data/test/Aleya/minimal.csv`

## Flujo de trabajo (KNIME)
```mermaid
flowchart LR
  A[File Reader (CSV)] --> B[Python Script]
  B --> C[Table View / JSON Output]
```

### Script (Python Script node)
- `from src.aleya.aleya import Aleya`
- `aleya = Aleya(); aleya.set_data(path)`
- Emitir tamaño (n filas) hacia la salida para validar = 3

## Pasos (KNIME)
1. Configura el entorno Python de KNIME apuntando a la misma venv.
2. Construye el flujo: File Reader → Python Script → Table View.
3. Ejecuta y comprueba que el conteo de filas sea 3.

## Notas
- Usa Flow Variables para parametrizar la ruta del CSV.
- Procura que los nodos no dependan de rutas absolutas.
