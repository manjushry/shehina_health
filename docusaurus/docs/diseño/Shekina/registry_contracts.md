---
title: Contratos del Registry (opcodes)
sidebar_position: 8
---

# Contratos del Registry

Esta página enumera opcodes soportados y la forma esperada de su `payload`, `inputs` y `outputs`. Sirve como contrato entre la tabla canónica y las implementaciones en el Registry.

## Mirror

- mirror.select_df
  - inputs: —
  - payload: `{ sql?: string, table?: string, where?: string }`
  - outputs: `["<df_name>"]` (p. ej., `"base_df"`)
- mirror.upsert_df
  - inputs: `["<df_name>"]`
  - payload: `{ table: string, keys: string[], mode?: "append"|"replace" }`
  - outputs: `["rows_written"]`
- mirror.update_from_dataframe
  - inputs: `["<df_name>"]`
  - payload: `{ table: string, keys: string[], set: string[] }`
  - outputs: `["rows_updated"]`

## AlchemistPrime

- alchemist.transmute
  - inputs: `["<df_name>"]`
  - payload: `{ steps: Array<Step> }`
  - outputs: `["<df_out>"]`
  - Step CLEAN_IDENTIFIER: `{ type: "CLEAN_IDENTIFIER", src: string, target: string, pattern?: string, replacement?: string }`
  - Step LOWERCASE: `{ type: "LOWERCASE", columns: string[] }`
  - Step JOIN: `{ type: "JOIN", left: string, right: string, on: string[] }`

## BereshitSQL

- bereshit.bootstrap
  - inputs: —
  - payload: `{ flags: string[], dry_run?: boolean }`
  - outputs: `["logs"]`
- bereshit.exec
  - inputs: —
  - payload: `{ sql: string }`
  - outputs: `["logs"]`

## DaathGraph (propuesta)

- daath.create_nodes
  - inputs: `["<df_nodes>"]`
  - payload: `{ label: string, key: string, props: string[] }`
  - outputs: `["nodes_created"]`
- daath.create_edges
  - inputs: `["<df_edges>"]`
  - payload: `{ type: string, from: {label: string, key: string}, to: {label: string, key: string}, props?: string[] }`
  - outputs: `["edges_created"]`

Notas
- Los nombres de outputs deben encadenar con los inputs de pasos subsecuentes.
- Cualquier implementación debe registrar estas firmas en el Registry y validar payloads.
