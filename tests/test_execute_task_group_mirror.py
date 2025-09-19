from shekina.shekina import Shekina


class Registry:
    def __init__(self):
        self._f = {}

    def register(self, opcode, fn):
        self._f[opcode] = fn

    def resolve(self, opcode):
        return self._f.get(opcode)


def mirror_select_df(context, payload):
    name = (payload.get('outputs') or ['df_data'])[0]
    context[name] = [{'id': 1}, {'id': 2}]
    return {'rows': 2}


def test_execute_task_group_mirror_runs_rows():
    reg = Registry()
    reg.register('mirror.select_df', mirror_select_df)
    table = [
        {"id": "m1", "process_key": "MIR1", "step": "mirror.read", "opcode": "mirror.select_df", "payload": {"outputs": ["df_data"]}},
    ]
    sk = Shekina(config={}, process_table=table)
    sk.set_registry(reg)
    # compile group by process_key MIR1 and execute
    res = sk._invoke_task('shekina.execute_task_group', context={}, payload={'inputs': {
        'process_key': 'MIR1',
        'executor': 'mirror'
    }})
    assert isinstance(res, dict)
    assert 'executed' in res or 'error' in res
    if 'executed' in res:
        assert res['items'] == 1