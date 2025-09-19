---
title: Caso 4 — Shekina → BereshitSQL
sidebar_position: 4
---

# Caso 4: Shekina → BereshitSQL

- Qué hace: pasos de inicialización/DDL con BereshitSQL (bootstrap, flags, seeds). En pruebas, ejecutar en modo dry-run.
- Objetivo: documentar y validar los contratos para inicialización del entorno.

## Tabla que recibe (esquema por paso)

- opcode: `bereshit.bootstrap` o `bereshit.exec`
- payload:
  - bootstrap: `{ flags: ["schemas", "tables", "seed?", ...], dry_run: true }`
  - exec: `{ sql: "CREATE TABLE ..." }`
- sin inputs/outputs obligatorios

Ejemplo:

```json
[
  { "id": "b1", "step": "bootstrap", "opcode": "bereshit.bootstrap", "payload": { "flags": ["schemas", "tables"], "dry_run": true } }
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
participant Bereshit as "BereshitSQL (callable)"
User->>Shekina: run_process_table(table)
Shekina->>Aleya: run(table)
Aleya->>Registry: resolve("bereshit.*")
Registry-->>Aleya: callable
Aleya->>Bereshit: execute(payload)
Bereshit-->>Aleya: logs
Aleya-->>Shekina: context, run_log
Shekina-->>User: run_log consolidado
```

## Tabla que entrega

- run_log con acciones aplicadas/omitidas.

## Notas

- Evita operaciones destructivas por defecto; usa `dry_run: true` en escenarios de prueba.
