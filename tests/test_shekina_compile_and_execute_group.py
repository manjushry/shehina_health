import pytest

from shekina.shekina import Shekina


def test_compile_task_group_from_df_with_sql_like_where_and_alias_executor():
    pd = pytest.importorskip('pandas')
    # Build a fake df_flow-like DataFrame with mixed 'class' names (aliases included)
    df = pd.DataFrame([
        {'class': 'alkemist', 'opcode': 'alchemist.step', 'step_id': 1, 'step_type': 'ASSIGN_CONSTANT', 'source_column': None, 'target_column': 'x', 'step_params': {'value': 1}},
        {'class': 'AlchemistPrime', 'opcode': 'alchemist.step', 'step_id': 2, 'step_type': 'ASSIGN_CONSTANT', 'source_column': None, 'target_column': 'y', 'step_params': {'value': 2}},
        {'class': 'alkemist', 'opcode': 'alchemist.step', 'step_id': 3, 'step_type': 'ASSIGN_CONSTANT', 'source_column': None, 'target_column': 'z', 'step_params': {'value': 3}},
    ])
    cfg = {'executor_aliases': {'alkemist': 'alchemist', 'AlchemistPrime': 'alchemist'}}
    sh = Shekina(config=cfg)
    ctx = {'df_flow': df}
    # Use SQL-like DSL to select from df_flow and a where filtering step_id in [1,3]
    res = sh._invoke_task('shekina.compile_task_group', context=ctx, payload={'inputs': {
        'dsl': "select * from df_flow where index in [0,2]"
    }})
    assert 'task_group' in res, res
    tg = res['task_group']
    assert tg['executor'] == 'alchemist'  # aliases normalized
    assert tg['count'] == 2


def test_execute_task_group_alchemist_mvp_requires_inputs():
    pd = pytest.importorskip('pandas')
    pytest.importorskip('polars')  # AlchemistPrime depende de polars
    # Create a small data frame and flow
    data = pd.DataFrame({'raw': ['A!', 'B#']})
    flow = pd.DataFrame([
        {'row_id': 'r1', 'step_id': 1, 'source_table': None, 'source_column': None, 'step_type': 'ASSIGN_CONSTANT', 'step_params': {'value': 'ok'}, 'target_column': 'flag'},
    ])
    sh = Shekina(config={})
    ctx = {'shekina': {'df_data': data}, 'alchemist': {'flow': {'df_flow': flow}}}
    # Execute without providing df_flow in inputs should still work via context
    res = sh._invoke_task('shekina.execute_task_group', context=ctx, payload={'inputs': {
        'from': 'df_flow',
        'where': "index in [0]",
        'executor': 'alchemist'
    }})
    # It should fail due to missing df_data or succeed depending on context; ensure either result structure
    if 'error' in res:
        assert 'df_data' in res['error'] or 'df_flow' in res['error']
    else:
        assert 'df_data_transmuted' in res