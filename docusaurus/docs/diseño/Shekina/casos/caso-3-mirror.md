---
title: Caso 3 — Shekina → Mirror
sidebar_position: 3
---

# Caso 3: Shekina → Mirror

- Qué hace: pasos de lectura/escritura usando Mirror (`mirror.select_df`, `mirror.upsert_df`, `mirror.update_from_dataframe`).
- Objetivo: validar que las operaciones de I/O se describen en la tabla y el Registry las resuelve correctamente.

## Tabla que recibe (esquema por paso)

- id, step, depends_on
- opcode: uno de `mirror.select_df`, `mirror.upsert_df`, `mirror.update_from_dataframe`
- payload: 
  - select_df: `{ sql: "SELECT ..." }` o `{ table: "name", where: "..." }`
  - upsert_df: `{ table: "name", keys: ["id"], mode?: "append|replace" }`
  - update_from_dataframe: `{ table: "name", keys: ["id"], set: ["col1", "col2"] }`
- inputs/outputs según corresponda

Ejemplo de filas:

```json
[
  { "id": "s1", "step": "lectura", "opcode": "mirror.select_df", "payload": { "sql": "SELECT id, name FROM src" }, "outputs": ["src_df"] },
  { "id": "s2", "step": "escritura", "depends_on": ["s1"], "opcode": "mirror.upsert_df", "payload": { "table": "target", "keys": ["id"] }, "inputs": ["src_df"], "outputs": ["rows_written"] }
]
```

## Diagrama de Secuencia

```mermaid
%%{init: { 'themeVariables': { 'primaryColor': '#1f77b4' } } }%%
sequenceDiagram
participant User
participant Shekina
participant Aleya
participant Registry
participant Mirror as "Mirror (callable)"
User->>Shekina: run_process_table(table)
Shekina->>Aleya: run(table)
Aleya->>Registry: resolve("mirror.*")
Registry-->>Aleya: callable
Aleya->>Mirror: execute(payload, inputs)
Mirror-->>Aleya: outputs (df o métricas)
Aleya-->>Shekina: context, run_log
Shekina-->>User: artefactos y log
```

## Tabla que entrega

- context: `src_df`, `rows_written`, etc.
- run_log por paso.

## Notas

- Define `keys` para upsert a fin de garantizar idempotencia.
- En modo demo, se puede simular `rows_written` como el número de filas en el input.
