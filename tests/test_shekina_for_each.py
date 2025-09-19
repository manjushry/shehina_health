import pytest


def _make_registry():
    class _DummyReg:
        def resolve(self, opcode):
            return None
    return _DummyReg()


def _mk_shekina():
    from shekina.shekina import Shekina
    sk = Shekina(config={'db_params': {}}, process_table=[])
    sk.set_registry(_make_registry())
    return sk


def test_for_each_cycle_detection_strict():
    pd = pytest.importorskip('pandas')
    sk = _mk_shekina()
    df = pd.DataFrame({
        'process_key': ['A', 'B'],
        'depends_on': [['B'], ['A']],
    })
    ctx = {'df': df}
    payload = {
        'inputs': {
            'dsl': "process_key in df",
        },
        'exec_mode': 'parallel',
        'strict_dependencies': True,
    }
    res = sk._invoke_task('shekina.for_each', context=ctx, payload=payload)
    assert isinstance(res, dict)
    assert 'error' in res
    assert 'Ciclo' in res['error']


def test_for_each_external_deps_disallowed():
    pd = pytest.importorskip('pandas')
    sk = _mk_shekina()
    df = pd.DataFrame({
        'process_key': ['A', 'B'],
        'depends_on': [['X'], []],  # X no existe
    })
    ctx = {'df': df}
    payload = {
        'inputs': {
            'dsl': "process_key in df",
        },
        'exec_mode': 'parallel',
        'allow_external_deps': False,
    }
    res = sk._invoke_task('shekina.for_each', context=ctx, payload=payload)
    assert isinstance(res, dict)
    assert 'error' in res
    assert 'externas' in res['error'].lower()
    assert 'details' in res


def test_for_each_period_range_sequential():
    sk = _mk_shekina()
    ctx = {}
    payload = {
        'inputs': {
            'dsl': "period in ('202401'..'202403') process_key='demo'",
        },
        'exec_mode': 'sequential',
    }
    res = sk._invoke_task('shekina.for_each', context=ctx, payload=payload)
    # Para secuencial, debe retornar un objeto con lista de items procesados
    assert isinstance(res, dict)
    assert 'for_each' in res
    items = res['for_each']
    assert isinstance(items, list)
    assert len(items) == 3  # 202401, 202402, 202403
