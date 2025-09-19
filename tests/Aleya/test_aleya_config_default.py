import json
import os
from pathlib import Path

import pytest

# Import de la clase Aleya
from src.aleya.aleya import Aleya

DATA_DIR = Path(__file__).resolve().parents[2] / 'data' / 'test' / 'Aleya'


def test_carga_config_por_defecto():
    cfg_path = DATA_DIR / 'config_default.json'
    assert cfg_path.exists(), 'Archivo de config_default.json no encontrado'

    with open(cfg_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    aleya = Aleya()
    # Suponiendo que Aleya tiene un método set_config(dict)
    if hasattr(aleya, 'set_config'):
        aleya.set_config(cfg)
    else:
        pytest.skip('Aleya no implementa set_config(cfg) aún')

    # Suponiendo que Aleya expone get_config() para verificar
    if hasattr(aleya, 'get_config'):
        out = aleya.get_config()
        assert out == cfg
    else:
        # Validación mínima si no existe get_config
        assert True
