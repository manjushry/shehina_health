import pytest

from src.shekina.shekina import Shekina


class Registry:
    def __init__(self):
        self._f = {}

    def register(self, opcode, fn):
        self._f[opcode] = fn

    def resolve(self, opcode):
        return self._f[opcode]


def mirror_select_df(context, payload):
    # For tests, expect payload to contain inline data list
    rows = payload.get("data", [])
    out_name = (payload.get("outputs") or [None])[0] or "base_df"
    # Standardize to list of dicts
    norm = [{"id": r["id"], "raw": r["raw"]} for r in rows]
    context[out_name] = norm
    return {"rows": len(norm)}


def alchemist_transmute(context, payload):
    inputs = payload.get("inputs") or ["base_df"]
    src_name = inputs[0]
    rows = list(context[src_name])
    steps = payload.get("steps", [])
    out = rows
    for st in steps:
        if st.get("type") == "CLEAN_IDENTIFIER":
            src = st.get("src", "raw")
            dst = st.get("target", "clean")
            pattern = st.get("pattern", "[^A-Za-z0-9]")
            repl = st.get("replacement", "")
            import re
            rx = re.compile(pattern)
            out = [
                {**r, dst: rx.sub(repl, str(r.get(src, "")).lower())}
                for r in out
            ]
    out_name = (payload.get("outputs") or [None])[0] or "clean_df"
    context[out_name] = out
    return {"rows": len(out)}


def test_shekina_run_process_table_alchemist_clean_identifier():
    registry = Registry()
    registry.register("mirror.select_df", mirror_select_df)
    registry.register("alchemist.transmute", alchemist_transmute)

    table = [
        {
            "id": "s1",
            "step": "load",
            "opcode": "mirror.select_df",
            "payload": {"data": [{"id": 1, "raw": "A!"}, {"id": 2, "raw": "B#"}], "outputs": ["base_df"]},
            "outputs": ["base_df"],
        },
        {
            "id": "s2",
            "step": "cleanup",
            "depends_on": ["load"],
            "opcode": "alchemist.transmute",
            "payload": {
                "inputs": ["base_df"],
                "steps": [{"type": "CLEAN_IDENTIFIER", "src": "raw", "target": "clean", "pattern": "[^A-Za-z0-9]", "replacement": ""}],
                "outputs": ["clean_df"],
            },
            "inputs": ["base_df"],
            "outputs": ["clean_df"],
        },
    ]

    shekina = Shekina(config={"db_params": {}}, process_table=None)
    context, run_log = shekina.run_process_table(table, registry=registry)

    assert "base_df" in context
    assert "clean_df" in context
    assert len(context["clean_df"]) == 2
    # cleaned values should remove non-alphanumeric and lower-case
    assert context["clean_df"][0]["clean"] == "a"
    assert context["clean_df"][1]["clean"] == "b"
    # run_log contains two ok entries
    assert [e["status"] for e in run_log].count("ok") == 2
