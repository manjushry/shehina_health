# DSL Cheatsheet (Shekina For-Each)

Este documento resume la DSL para declarar iteraciones en Shekina usando una tabla de flujo única.

## Formas de iteración

- Periodos explícitos:
  - dsl: `period in ('202401','202402') process_key='mi_proceso'`
  - dsl: `periodo in ('202401'..'202403') process_key='mi_proceso'`
- Iteración por tabla:
  - dsl: `process_key in df_flow`
  - dsl: `fila in df_tabla where status == 'OK' || tipo in ['X','Y']`

## Where avanzado (tabla)
- `col == expr` donde `expr` admite concatenación con `+` y referencias `context.*`
- `col in ['a','b']` y `index in [1,2,3]`
- OR con `||` para combinar condiciones

## Paralelismo y dependencias
- `exec_mode`: `sequential` (por defecto) o `parallel`
- `depends_on`: si la tabla iterada tiene columna `depends_on`, se respeta con scheduler por olas (tipo Kahn)
- Flags:
  - `strict_dependencies` (bool): si hay ciclos, falla cuando `True`; por defecto `False` (mejor esfuerzo: ejecuta la última ola con el ciclo)
  - `allow_external_deps` (bool): si `False`, fallará cuando haya dependencias a items fuera del universo iterado; por defecto `True` (se ignoran)

## Contexto y variables
- `periodo` y `shekina.current_periodo` se fijan en el contexto hijo
- La variable de iteración (p. ej. `process_key`) se expone en el contexto hijo con su valor
- `process_key` puede fijarse en el DSL con `process_key='...'` o inferirse cuando la variable iterada se llama `process_key`
 - `business_process` (o `bussiness_process`) en inputs/global: permite filtrar/compilar un grupo de subtareas (equivalente a process_key)

## Ejemplos

- Procesar 202401..202403 en paralelo:
  - inputs:
    - dsl: `period in ('202401'..'202403') process_key='transmute__citas_fin_ajustadas'`
  - exec_mode: `parallel`

- Iterar process_keys con dependencias por olas:
  - inputs:
    - dsl: `process_key in df_flow where step_type == 'TRANSFORM'`
  - exec_mode: `parallel`
  - strict_dependencies: `true`
  - allow_external_deps: `false`

## Tareas utilitarias
- `shekina.compile_task_group`: alias genérico para compilar/agrupar subtareas (equivale a `shekina.compile_alchemist_flow` hoy)
  - Acepta inputs estilo SQL: `dsl: "select * from df_flow where step_type == 'ASSIGN_CONSTANT' || index in [1,3]"`
  - Alternativamente, usar `inputs.from` + `inputs.where`, o `process_key|business_process` desde la tabla canónica.
  - Enforce por defecto una única clase ejecutora por grupo (`class_lock=true`), configurable via `inputs.executor` o `class_lock=false`.

- `shekina.execute_task_group`: compila y ejecuta el grupo según su ejecutor. MVP: `alchemist`.
  - Usa `df_flow` compilado y `df_data`/`df_dict` del contexto o de `inputs`.
  - Coloca resultados en `context.alchemist.last_run.*` y retorna `df_data_transmuted` y `ap`.

- `shekina.end`: marcador de fin de subproceso (no-op), útil para delimitar bloques en tablas largas

### Ejecutores no-Alchemist y configuración

- Ejecutores como `mirror` o `daath` usan por defecto la estrategia `run_rows`, que ejecuta directamente las filas del grupo usando `run_process_table` (y el `registry`) respetando dependencias.
- Este comportamiento, junto con los alias de ejecutor, se configura en `src/shekina/config-class.json`:
  - `executor_aliases`: define equivalencias de nombres (ej. `alkemist` → `alchemist`).
  - `executors`: mapea el ejecutor a una `strategy` (`internal_alchemist` o `run_rows`).
