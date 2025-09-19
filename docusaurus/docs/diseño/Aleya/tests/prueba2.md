title: Aleya - Prueba 2 · Carga de dataset mínimo

## test_id
Aleya/test/prueba2

## Objetivo
Validar que Aleya carga un dataset mínimo de 3 filas y lo deja accesible.

## Inputs
- `data/test/Aleya/minimal.csv`

## Procedimiento (pytest)
```
pytest -q tests/Aleya/test_aleya_load_minimal.py::test_carga_datos_minimos
```

## Resultado esperado
- El atributo de datos accesible (`data`/`df`/`dataset`) posee 3 registros.

## Código de prueba
Ruta: `tests/Aleya/test_aleya_load_minimal.py`

```python
from pathlib import Path
from src.aleya.aleya import Aleya

DATA_DIR = Path(__file__).resolve().parents[3] / 'data' / 'test' / 'Aleya'

def test_carga_datos_minimos():
    csv_path = DATA_DIR / 'minimal.csv'
    aleya = Aleya()
    aleya.set_data(str(csv_path))
    assert hasattr(aleya, 'data') or hasattr(aleya, 'df') or hasattr(aleya, 'dataset')
```

## Diagrama de secuencia

```mermaid
sequenceDiagram
    participant VSCode as VS Code / Pytest
    participant Aleya
    VSCode->>Aleya: set_data(minimal.csv)
    Aleya->>Aleya: validar esquema/filas
    Aleya-->>VSCode: exponer datos en atributo (data/df)
```

## Diagrama de flujo

```mermaid
flowchart LR
    A[Leer minimal.csv] --> B[Instanciar Aleya]
    B --> C["Llamar set_data(csv)"]
    C --> D{Carga exitosa?}
    D -- Sí --> E[Acceso al atributo de datos]
    E --> F[Validar 3 filas]
    D -- No --> X[Error o skip]
```

## VSCode

### Inputs
- `data/test/Aleya/minimal.csv`

### Ambiente
```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest
```

### Pasos
```
pytest -q tests\Aleya\test_aleya_load_minimal.py::test_carga_datos_minimos
```

## KNIME

### Inputs
- File Reader con `data/test/Aleya/minimal.csv`

### Script / Flujo
- Nodo Python Script:
    - from src.aleya.aleya import Aleya
    - aleya = Aleya(); aleya.set_data(path)
    - Exponer tamaño (n filas) a salida de tabla para validar=3

### Pasos
1. Configurar entorno Python de KNIME apuntando a la misma venv.
2. Crear flujo: File Reader → Python Script → Table View.
3. Ejecutar y validar 3 filas.
