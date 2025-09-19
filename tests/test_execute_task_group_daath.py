from shekina.shekina import Shekina


def test_internal_daath_unresolved_and_conflict_plan():
    # Config con estrategia internal_daath (viene por defecto en config-class.json)
    sk = Shekina(config={})
    ctx = {}
    inputs = {
        'executor': 'daath',
        'columns': ['doc_id', 'numero_paciente', 'numero_documento', 'genero'],
        'canonical_map': {
            'numero_documento': ['doc_id', 'numero_paciente']
        },
        'canonical_set': ['numero_documento', 'sexo'],
        'col_stats': {
            'doc_id': {'percent_numeric': 0.9, 'percent_null': 0.1},
            'numero_paciente': {'percent_numeric': 0.1, 'percent_null': 1.0},
        },
        'source_domain': 'fomag__capital_general__202509',
        'auto_upsert': False,
    }
    # items vacíos: solo usamos executor y columnas + mapas
    res = sk._invoke_task('shekina.execute_task_group', context=ctx, payload={'inputs': inputs})
    assert isinstance(res, dict)
    # Debe haber error por 'genero' sin sinónimo y conflicto para 'numero_documento'
    assert res.get('status_pk') == 'error'
    assert 'genero' in (res.get('unresolved') or [])
    conflicts = res.get('conflicts') or []
    # Conflicto reportado con recomendación 'usar doc_id'
    has_conflict = any(cf.get('canonical') == 'numero_documento' and 'doc_id' in cf.get('columns', []) for cf in conflicts)
    assert has_conflict
    up = (res.get('upsert_plan') or {})
    assert 'nodes' in up and 'edges' in up