from src.shekina.shekina import Shekina


class Registry:
    def __init__(self):
        self._f = {}

    def register(self, opcode, fn):
        self._f[opcode] = fn

    def resolve(self, opcode):
        return self._f[opcode]


def mirror_select_df(context, payload):
    rows = payload.get("data", [])
    out = [{"id": r["id"], "name": r.get("name", "")} for r in rows]
    out_name = (payload.get("outputs") or [None])[0] or "src_df"
    context[out_name] = out
    return {"rows": len(out)}


def mirror_upsert_df(context, payload):
    inputs = payload.get("inputs") or ["src_df"]
    src = inputs[0]
    rows = context.get(src, [])
    # Simulate upsert by counting
    written = len(rows)
    out_name = (payload.get("outputs") or [None])[0] or "rows_written"
    context[out_name] = written
    return {"rows_written": written}


def test_shekina_mirror_read_write():
    registry = Registry()
    registry.register("mirror.select_df", mirror_select_df)
    registry.register("mirror.upsert_df", mirror_upsert_df)

    table = [
        {
            "id": "s1",
            "step": "read",
            "opcode": "mirror.select_df",
            "payload": {"data": [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}], "outputs": ["src_df"]},
            "outputs": ["src_df"],
        },
        {
            "id": "s2",
            "step": "write",
            "depends_on": ["read"],
            "opcode": "mirror.upsert_df",
            "payload": {"inputs": ["src_df"], "outputs": ["rows_written"], "table": "target", "keys": ["id"]},
            "inputs": ["src_df"],
            "outputs": ["rows_written"],
        },
    ]

    shekina = Shekina(config={"db_params": {}}, process_table=None)
    context, run_log = shekina.run_process_table(table, registry=registry)

    assert context.get("rows_written") == 2
    assert [e["status"] for e in run_log].count("ok") == 2
