title: Aleya - Prueba 1 · Carga de configuración por defecto

## test_id
Aleya/test/prueba1

## Objetivo
Validar que Aleya acepta una configuración por defecto y la expone correctamente.

## Inputs
- `data/test/Aleya/config_default.json`

## Procedimiento (pytest)
```
pytest -q tests/Aleya/test_aleya_config_default.py::test_carga_config_por_defecto
```

## Resultado esperado
- `get_config()` devuelve el mismo diccionario cargado.

## Código de prueba
Ruta: `tests/Aleya/test_aleya_config_default.py`

```python
from pathlib import Path
import json
from src.aleya.aleya import Aleya

DATA_DIR = Path(__file__).resolve().parents[3] / 'data' / 'test' / 'Aleya'

def test_carga_config_por_defecto():
    cfg_path = DATA_DIR / 'config_default.json'
    cfg = json.loads(cfg_path.read_text(encoding='utf-8'))
    aleya = Aleya()
    aleya.set_config(cfg)
    assert aleya.get_config() == cfg
```

## Diagrama de secuencia

```mermaid
sequenceDiagram
    participant VSCode as VS Code / Pytest
    participant Aleya
    VSCode->>Aleya: set_config(config_default.json)
    Aleya->>Aleya: validar estructura del dict
    Aleya-->>VSCode: get_config() == config
```

## Diagrama de flujo

```mermaid
flowchart TD
    A[Leer config_default.json] --> B[Instanciar Aleya]
    B --> C[Llamar set_config(cfg)]
    C --> D{Estructura válida?}
    D -- Sí --> E[Obtener get_config]
    E --> F[Comparar igualdad]
    D -- No --> X[Error o fallback]
```

## VSCode

### Inputs
- `data/test/Aleya/config_default.json`

### Ambiente
```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
pip install pytest
```

### Pasos
```
pytest -q tests\Aleya\test_aleya_config_default.py::test_carga_config_por_defecto
```

## KNIME

### Inputs
- File Reader (o nodo Python) con `data/test/Aleya/config_default.json`

### Script / Flujo
- Nodo Python Script:
    - Cargar JSON
    - from src.aleya.aleya import Aleya
    - Instanciar y llamar `set_config(cfg)` y `get_config()`
    - Emitir resultado a tabla/JSON equivalente

### Pasos
1. Configurar entorno Python de KNIME apuntando a la misma venv del repo.
2. Crear flujo: File Reader → Python Script → Table View.
3. Ejecutar y validar igualdad del diccionario.
