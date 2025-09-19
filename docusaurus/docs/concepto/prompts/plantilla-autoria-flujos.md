# Plantilla de Autoría de Flujos (PSV)

Usa esta plantilla para describir flujos en una única tabla con separador `|` y la DSL de `shekina.for_each`.

## Sección s0: init y asignaciones
- class: `shekina`, opcode: `init`
- inputs.assign: lista de asignaciones con opcional `AS alias`

Ejemplo:
- step: `s0`
- class: `shekina`
- opcode: `init`
- inputs:
  - assign:
    - `shekina.periodo_inicio = '202401'`
    - `shekina.periodo_fin = '202403'`
    - `alchemist.flow = context.alchemist.flow.df_flow AS df_flow`

## Sección s1: iteración por periodos o tabla
- class: `shekina`, opcode: `for_each`
- inputs.dsl:
  - Periodos: `period in ('202401'..'202403') process_key='mi_proceso'`
  - Tabla: `process_key in df_flow where step_type == 'TRANSFORM'`
- exec_mode: `parallel` o `sequential`
- Flags opcionales: `strict_dependencies`, `allow_external_deps`, `max_workers`

## Agrupar subtareas por proceso (business_process)
- Puedes declarar `business_process` (o `bussiness_process`) en `inputs` para indicar el bloque de subtareas a compilar/ejecutar (equivalente a `process_key`).
- Usa `shekina.compile_task_group` (o `shekina.compile_alchemist_flow`) para construir la lista de subtareas de ese grupo.
- Opcional: añade `shekina.end` como marcador de cierre.

## Sección s2: compilar df_flow (si aplica)
- class: `shekina`, opcode: `compile_task_group` (alias de `compile_alchemist_flow`)
- inputs.business_process: `mi_proceso` (o `process_key`)
- outputs: `alchemist.flow`

## Sección rXX: pasos Alchemist
- class: `alchemist`, opcode: `step`
- process_key: `mi_proceso`
- payload.step_type, payload.source_column, payload.target_column, payload.step_params

## Tips
- Usa alias/assign para exponer `df_flow/df_data/df_dict` en `context`.
- Si iteras por `process_key in df_flow`, cada hijo fijará `process_key` automáticamente.
- Declara `depends_on` por fila en `df_flow` para que el scheduler por olas respete dependencias.
