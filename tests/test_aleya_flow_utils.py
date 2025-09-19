import pytest


def test_compile_alchemist_flow_filters_and_shape():
    pd = pytest.importorskip('pandas')
    from aleya.flow_utils import compile_alchemist_flow

    process_table = [
        {'id': 'r1', 'process_key': 'P1', 'opcode': 'alchemist.step', 'payload': {
            'step_id': 2, 'step_type': 'ASSIGN_CONSTANT', 'source_column': None, 'target_column': 'x', 'step_params': {'value': 1}
        }},
        {'id': 'r2', 'process_key': 'P2', 'opcode': 'alchemist.step', 'payload': {
            'step_id': 1, 'step_type': 'ASSIGN_CONSTANT', 'source_column': None, 'target_column': 'y', 'step_params': {'value': 2}
        }},
        {'id': 'r3', 'process_key': 'P1', 'opcode': 'alchemist.step', 'payload': {
            'step_id': 3, 'step_type': 'ASSIGN_CONSTANT', 'source_column': None, 'target_column': 'z', 'step_params': {'value': 3}
        }},
        {'id': 'r4', 'process_key': 'P1', 'opcode': 'noop', 'payload': {}},
    ]

    res = compile_alchemist_flow(process_table, filter_process_key='P1')
    assert 'df_flow' in res, res
    df = res['df_flow']
    assert list(df.columns) == ['row_id', 'step_id', 'source_table', 'source_column', 'step_type', 'step_params', 'target_column']
    # Debe contener sólo r1 y r3 (P1), ordenado por step_id asc (2,3)
    assert df.shape[0] == 2
    assert df['step_id'].tolist() == [2, 3]


def test_build_dependency_waves_basic_and_errors():
    from aleya.flow_utils import build_dependency_waves

    # Caso básico: A depende de B; B sin deps; C independiente
    deps = {
        'A': {'B'},
        'B': set(),
        'C': set()
    }
    waves = build_dependency_waves(deps, allow_external_deps=True, strict_dependencies=False)
    assert 'levels' in waves
    levels = waves['levels']
    # Primera ola: B y C (ambos sin deps); segunda ola: A
    assert any('B' in lvl for lvl in levels)
    assert any('C' in lvl for lvl in levels)
    assert any('A' in lvl for lvl in levels)

    # Externas no permitidas
    deps2 = {'X': {'Y'}}  # Y no está en universo
    err = build_dependency_waves(deps2, allow_external_deps=False, strict_dependencies=False)
    assert 'error' in err and 'externas' in err['error'].lower()

    # Ciclo con strict
    deps3 = {'A': {'B'}, 'B': {'A'}}
    err2 = build_dependency_waves(deps3, allow_external_deps=True, strict_dependencies=True)
    assert 'error' in err2 and 'Ciclo' in err2['error']
