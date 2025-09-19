import React, {useMemo, useState} from 'react';
// Mermaid React component provided by the theme for dynamic charts
// https://docusaurus.io/docs/markdown-features/diagrams#using-mermaid-in-react
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import Mermaid from '@theme/Mermaid';

type Step = {
  id: string;
  step: string;
  depends_on?: string[];
  enabled?: boolean;
  opcode: string;
  condition?: unknown;
  payload?: Record<string, unknown>;
  inputs?: string[];
  outputs?: string[];
};

const DEFAULT_JSON = `[
  {
    "id": "s1",
    "step": "load_base",
    "depends_on": [],
    "enabled": true,
    "opcode": "mirror.select_df",
    "payload": {"sql": "SELECT 1 AS id, 'A' AS raw UNION ALL SELECT 2, 'B'"},
    "outputs": ["base_df"],
    "retries": 0,
    "timeout_s": 10
  },
  {
    "id": "s2",
    "step": "cleanup",
    "depends_on": ["load_base"],
    "enabled": true,
    "opcode": "alchemist.transmute",
    "payload": {
      "engine": "polars",
      "steps": [
        {"type": "CLEAN_IDENTIFIER", "src": "raw", "target": "clean", "pattern": "[^A-Za-z0-9]", "replacement": ""}
      ]
    },
    "inputs": ["base_df"],
    "outputs": ["clean_df"],
    "retries": 0,
    "timeout_s": 10
  },
  {
    "id": "s3",
    "step": "skip_demo",
    "depends_on": ["cleanup"],
    "enabled": true,
    "opcode": "mirror.upsert_df",
    "condition": {"==": [1, 2]},
    "payload": {"table": "demo.out", "keys": ["id"]},
    "inputs": ["clean_df"],
    "outputs": ["rows_written"],
    "retries": 0,
    "timeout_s": 10
  }
]`;

function toposortLevels(steps: Step[]): string[][] {
  // Use step name as node key for edges, but levels display by id
  const nameToId = new Map(steps.map(s => [s.step, s.id] as const));
  const indegree = new Map<string, number>();
  const graph = new Map<string, string[]>();

  for (const s of steps) {
    indegree.set(s.id, 0);
    graph.set(s.id, []);
  }
  for (const s of steps) {
    const deps = s.depends_on ?? [];
    for (const depName of deps) {
      const from = nameToId.get(depName);
      if (!from) continue; // ignore unknown deps
      graph.get(from)!.push(s.id);
      indegree.set(s.id, (indegree.get(s.id) ?? 0) + 1);
    }
  }

  const q: string[] = [];
  for (const [node, deg] of indegree.entries()) {
    if (deg === 0) q.push(node);
  }
  const levels: string[][] = [];
  let idx = 0;
  while (q.length) {
    const currLevel = [...q];
    levels.push(currLevel);
    q.length = 0;
    for (const u of currLevel) {
      for (const v of graph.get(u) ?? []) {
        indegree.set(v, (indegree.get(v) ?? 0) - 1);
        if ((indegree.get(v) ?? 0) === 0) q.push(v);
      }
    }
    if (++idx > steps.length + 5) break; // safety
  }
  return levels;
}

function buildMermaid(steps: Step[]): string {
  const nameToId = new Map(steps.map(s => [s.step, s.id] as const));
  const lines: string[] = ['flowchart LR'];
  // Nodes
  for (const s of steps) {
    const label = `${s.id}: ${s.opcode}`.replaceAll('"', '\\"');
    lines.push(`  ${s.id}["${label}"]`);
  }
  // Edges
  for (const s of steps) {
    for (const depName of s.depends_on ?? []) {
      const from = nameToId.get(depName);
      if (from) lines.push(`  ${from} --> ${s.id}`);
    }
  }
  // Conditions
  for (const s of steps) {
    if (s.condition) {
      const cId = `C_${s.id}`;
      const skipId = `SKIP_${s.id}`;
      lines.push(`  ${cId}{"condition"}`);
      // Wire the last dependency (or leave floating)
      const lastDep = (s.depends_on ?? []).slice(-1)[0];
      const from = lastDep ? nameToId.get(lastDep) : undefined;
      if (from) lines.push(`  ${from} --> ${cId}`);
      lines.push(`  ${cId} -- true --> ${s.id}`);
      lines.push(`  ${cId} -- false --> ${skipId}["skipped"]`);
    }
  }
  return lines.join('\n');
}

export default function NotebookPlayground(): React.ReactElement {
  const [text, setText] = useState<string>(DEFAULT_JSON);
  const [useEditorData, setUseEditorData] = useState<boolean>(true);
  const [inputRows, setInputRows] = useState<Array<{id: number | string; raw: string}>>([
    {id: 1, raw: 'A'},
    {id: 2, raw: 'B'},
  ]);
  const [execResult, setExecResult] = useState<{
    clean_df?: Array<Record<string, any>>;
    rows_written?: number;
    run_log?: Array<{id: string; step: string; status: string; info?: string}>;
  }>({});

  const {error, steps, levels, chart} = useMemo(() => {
    try {
      const parsed: Step[] = JSON.parse(text);
      const lv = toposortLevels(parsed);
      const ch = buildMermaid(parsed);
      return {error: undefined, steps: parsed, levels: lv, chart: ch};
    } catch (e: any) {
      return {error: String(e), steps: [], levels: [], chart: 'flowchart LR'};
    }
  }, [text]);

  function evalCondition(cond: any): boolean {
    if (!cond) return true;
    // minimal jsonlogic: only {"==": [a,b]}
    if (typeof cond === 'object' && cond !== null && '==' in cond) {
      const arr = (cond as any)['=='];
      if (Array.isArray(arr) && arr.length === 2) {
        return String(arr[0]) === String(arr[1]);
      }
    }
    return Boolean(cond);
  }

  function parseSelectSql(sql?: string): Array<{id: number | string; raw: string}> {
    // Very tiny parser for the demo default: SELECT 1 AS id, 'A' AS raw UNION ALL SELECT 2, 'B'
    if (!sql) return [];
    const parts = sql.split(/UNION ALL/i);
    const rows: Array<{id: number | string; raw: string}> = [];
    for (const p of parts) {
      const m = p.match(/SELECT\s+(\d+)\s+AS\s+id\s*,\s*'([^']+)'\s+AS\s+raw/i) || p.match(/SELECT\s+(\d+)\s*,\s*'([^']+)'/i);
      if (m) rows.push({id: Number(m[1]), raw: m[2]});
    }
    return rows;
  }

  function onAddRow() {
    const nextId = inputRows.length ? Number(inputRows[inputRows.length - 1].id) + 1 : 1;
    setInputRows([...inputRows, {id: nextId, raw: ''}]);
  }
  function onRemoveRow(idx: number) {
    const copy = [...inputRows];
    copy.splice(idx, 1);
    setInputRows(copy);
  }

  function runPipeline() {
    try {
      const parsed: Step[] = JSON.parse(text);
      // context by output name -> data
      const context: Record<string, any> = {};
      const run_log: Array<{id: string; step: string; status: string; info?: string}> = [];

      // Execute in topo order (flatten levels)
      const flat: string[] = levels.flat();
      const idToStep = new Map(parsed.map(s => [s.id, s] as const));
      for (const id of flat) {
        const s = idToStep.get(id);
        if (!s) continue;
        const enabled = s.enabled !== false;
        if (!enabled) {
          run_log.push({id: s.id, step: s.step, status: 'disabled'});
          continue;
        }
        // Resolve inputs
        const inputsData = (s.inputs ?? []).map(name => context[name]);

        // Condition (if defined)
        const shouldRun = evalCondition((s as any).condition);
        if (!shouldRun) {
          run_log.push({id: s.id, step: s.step, status: 'skipped'});
          continue;
        }

        // Dispatch
        if (s.opcode === 'mirror.select_df') {
          let rows: Array<{id: number | string; raw: string}> = [];
          if (useEditorData && inputRows.length) {
            rows = inputRows;
          } else if ((s.payload as any)?.data) {
            rows = ((s.payload as any).data as Array<any>).map((r) => ({id: r.id, raw: r.raw}));
          } else {
            rows = parseSelectSql((s.payload as any)?.sql);
          }
          // output
          const outName = s.outputs?.[0] ?? 'base_df';
          context[outName] = rows;
          run_log.push({id: s.id, step: s.step, status: 'ok', info: `${rows.length} rows`});
        } else if (s.opcode === 'alchemist.transmute') {
          const rows: Array<Record<string, any>> = (inputsData[0] ?? []) as any[];
          const payload = (s.payload ?? {}) as any;
          const stepsSpec: Array<any> = payload.steps ?? [];
          let out = rows.map(r => ({...r}));
          for (const st of stepsSpec) {
            if (st?.type === 'CLEAN_IDENTIFIER') {
              const pattern = new RegExp(st.pattern ?? '[^A-Za-z0-9]', 'g');
              const src = st.src ?? 'raw';
              const dst = st.target ?? 'clean';
              out = out.map(r => ({...r, [dst]: String(r[src] ?? '').replace(pattern, st.replacement ?? '')}));
            }
          }
          const outName = s.outputs?.[0] ?? 'clean_df';
          context[outName] = out;
          run_log.push({id: s.id, step: s.step, status: 'ok', info: `${out.length} rows`});
        } else if (s.opcode === 'mirror.upsert_df') {
          const rows: Array<Record<string, any>> = (inputsData[0] ?? []) as any[];
          const outName = s.outputs?.[0] ?? 'rows_written';
          const written = rows.length;
          context[outName] = written;
          run_log.push({id: s.id, step: s.step, status: 'ok', info: `${written} rows_written`});
        } else {
          run_log.push({id: s.id, step: s.step, status: 'unknown-opcode'});
        }
      }

      setExecResult({
        clean_df: context['clean_df'],
        rows_written: context['rows_written'],
        run_log,
      });
    } catch (e: any) {
      setExecResult({
        run_log: [{id: 'error', step: 'pipeline', status: 'error', info: String(e)}],
      });
    }
  }

  return (
    <div style={{border: '1px solid var(--ifm-color-emphasis-300)', borderRadius: 8, padding: 16, marginTop: 16}}>
      <h3 style={{marginTop: 0}}>Playground interactivo</h3>
      <p style={{marginTop: 0}}>Edita el JSON de la tabla canónica, cambia los datos de entrada y observa niveles (DAG), diagrama y resultados de salida.</p>
      <details>
        <summary>Datos de entrada (base_df) — editor simple</summary>
        <div style={{margin: '8px 0'}}>
          <label style={{display: 'inline-flex', alignItems: 'center', gap: 8}}>
            <input type="checkbox" checked={useEditorData} onChange={(e) => setUseEditorData(e.target.checked)} />
            Usar este editor de datos para mirror.select_df
          </label>
        </div>
        <div style={{overflowX: 'auto'}}>
          <table className="table">
            <thead>
              <tr>
                <th>id</th>
                <th>raw</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {inputRows.map((r, idx) => (
                <tr key={idx}>
                  <td>
                    <input
                      value={r.id}
                      onChange={(e) => {
                        const copy = [...inputRows];
                        copy[idx] = {...copy[idx], id: e.target.value};
                        setInputRows(copy);
                      }}
                      style={{width: 100}}
                    />
                  </td>
                  <td>
                    <input
                      value={r.raw}
                      onChange={(e) => {
                        const copy = [...inputRows];
                        copy[idx] = {...copy[idx], raw: e.target.value};
                        setInputRows(copy);
                      }}
                      style={{width: 180}}
                    />
                  </td>
                  <td>
                    <button className="button button--sm button--danger" onClick={() => onRemoveRow(idx)}>Remover</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <button className="button button--sm button--secondary" onClick={onAddRow}>Agregar fila</button>
        </div>
      </details>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        style={{width: '100%', height: 220, fontFamily: 'var(--ifm-font-family-monospace)'}}
      />
      <div style={{display: 'flex', gap: 8, alignItems: 'center', margin: '8px 0'}}>
        <button className="button button--primary" onClick={runPipeline}>Ejecutar</button>
      </div>
      {error && (
        <div style={{color: 'var(--ifm-color-danger)'}}>
          Error al parsear JSON: {error}
        </div>
      )}
      {!error && (
        <>
          <div style={{marginTop: 8}}>
            <strong>Niveles (toposort por lotes):</strong>
            <pre style={{background: 'var(--ifm-pre-background)', padding: 8}}>{JSON.stringify(levels, null, 2)}</pre>
          </div>
          <div style={{marginTop: 8}}>
            <strong>Diagrama (Mermaid):</strong>
            <Mermaid value={chart} />
          </div>
          <div style={{marginTop: 8}}>
            <strong>Resultados:</strong>
            <div style={{display: 'flex', gap: 24, flexWrap: 'wrap'}}>
              <div>
                <div><em>clean_df</em></div>
                <div style={{overflowX: 'auto'}}>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>id</th>
                        <th>raw</th>
                        <th>clean</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(execResult.clean_df ?? []).map((r, i) => (
                        <tr key={i}>
                          <td>{String(r.id ?? '')}</td>
                          <td>{String(r.raw ?? '')}</td>
                          <td>{String(r.clean ?? '')}</td>
                        </tr>
                      ))}
                      {(!execResult.clean_df || execResult.clean_df.length === 0) && (
                        <tr><td colSpan={3} style={{textAlign: 'center'}}>—</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
              <div>
                <div><em>rows_written</em></div>
                <div>{execResult.rows_written ?? '—'}</div>
              </div>
            </div>
            <div style={{marginTop: 8}}>
              <em>run_log</em>
              <div style={{overflowX: 'auto'}}>
                <table className="table">
                  <thead>
                    <tr>
                      <th>id</th>
                      <th>step</th>
                      <th>status</th>
                      <th>info</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(execResult.run_log ?? []).map((r, i) => (
                      <tr key={i}>
                        <td>{r.id}</td>
                        <td>{r.step}</td>
                        <td>{r.status}</td>
                        <td>{r.info ?? ''}</td>
                      </tr>
                    ))}
                    {(!execResult.run_log || execResult.run_log.length === 0) && (
                      <tr><td colSpan={4} style={{textAlign: 'center'}}>—</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div style={{marginTop: 8}}>
            <strong>Resumen de pasos:</strong>
            <ul>
              {steps.map((s) => (
                <li key={s.id}>
                  <code>{s.id}</code> — <code>{s.step}</code> — <code>{s.opcode}</code>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  );
}
