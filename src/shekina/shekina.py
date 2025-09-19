import os
import re
import json
import warnings
from typing import Any, Dict, List, Optional, Tuple


class Shekina:
    """
    Orquestador principal entre el dominio (Shekina) y componentes de ejecución (Aleya runner,
    Registry de acciones, DaathGraph y BereshitSQL/Mirror para I/O).

    Preferir run_process_table con una tabla canónica (pipe-delimited) y opcodes.
    """

    def __init__(self, config: Dict[str, Any], process_table: Optional[List[Dict[str, Any]]] = None):
        self.config = config
        self.process_table = process_table
        self.daath = None
        self.bereshit = None
        self.aleya = None  # Runner de procesos (DAG)
        self.registry = None  # Catálogo de acciones (opcodes)
        self._current_table: Optional[List[Dict[str, Any]]] = None
        self._current_process_key: Optional[str] = None

    # Inyección de dependencias (opcional)
    def set_aleya(self, aleya: Any):
        self.aleya = aleya

    def set_registry(self, registry: Any):
        self.registry = registry

    # --- Métodos de legado mínimos ---
    def init_daath(self):
        try:
            from daath.daath_graph import DaathGraph
        except Exception as ex:
            raise ImportError("DaathGraph no disponible. Instale dependencias de grafo.") from ex
        self.daath = DaathGraph(db_params=self.config['db_params'])

    def init_bereshit(self):
        sql_dir = self.config.get('sql_dir', os.path.join(os.path.dirname(__file__), '..', 'alchemist', 'bereshit_sql'))
        try:
            from bereshit.bereshit_sql import BereshitSQL
        except Exception as ex:
            raise ImportError("BereshitSQL no disponible. Instale dependencias de base de datos.") from ex
        self.bereshit = BereshitSQL(self.config['db_params'], db_type='postgresql', sql_dir=sql_dir)

    def run_bootstrap(self):
        self.init_bereshit()
        self.bereshit.bootstrap()

    def run_etl(self):
        pass

    def query_grafo(self, cypher_query):
        if not self.daath:
            self.init_daath()
        return self.daath.query_cypher(cypher_query)

    # --- Orquestación basada en tabla canónica ---
    def run_process_table(self, table: List[Dict[str, Any]], registry: Optional[Any] = None, process_key: Optional[str] = None, initial_context: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Ejecuta una tabla canónica de procesos. Si existe un runner (Aleya) inyectado,
        se delega en él. De lo contrario, usa un runner mínimo incorporado.

        Retorna: (context, run_log)
        """
        reg = registry or self.registry

        # Permitir filtrar por process_key para reutilizar una tabla única
        full_table = table
        if process_key is not None:
            full_table = [row for row in table if row.get('process_key') == process_key]
            if not full_table:
                raise ValueError(f"No hay filas para process_key='{process_key}' en la tabla de procesos.")
        # Guardar contexto de ejecución actual para invocaciones internas
        self.process_table = table  # conservar referencia a la tabla original completa
        self._current_table = full_table
        self._current_process_key = process_key
        if self.aleya and hasattr(self.aleya, 'run'):
            if reg is None:
                raise ValueError("Registry no proporcionado. Usa set_registry() o pasa 'registry' en la llamada.")
            result = self.aleya.run(full_table, reg)
            if isinstance(result, tuple) and len(result) >= 2:
                return result[0], result[1]
            raise RuntimeError("La implementación de Aleya.run no devolvió (context, run_log, ...)")

        # Fallback: runner simple (sin paralelismo real)
        if reg is None:
            raise ValueError("Registry no proporcionado para el runner simple.")

        levels, by_id = self._compile_levels(full_table)
        context: Dict[str, Any] = dict(initial_context) if isinstance(initial_context, dict) else {}
        run_log: List[Dict[str, Any]] = []
        for lvl in levels:
            for sid in lvl:
                s = by_id[sid]
                if not s.get('enabled', True):
                    run_log.append({'id': s['id'], 'step': s['step'], 'status': 'disabled'})
                    continue
                if not self._eval_condition(s.get('condition')):
                    run_log.append({'id': s['id'], 'step': s['step'], 'status': 'skipped'})
                    continue
                payload = dict(s.get('payload', {}))
                # Propagar inputs declarados en la fila a payload.inputs
                if 'inputs' in s and s['inputs'] not in (None, ''):
                    payload['inputs'] = s['inputs']
                # Resolver opcode basado en columnas 'class' y 'opcode' para mayor intuición
                step_class = s.get('class') or s.get('clazz') or s.get('component')
                opcode = s.get('opcode')
                if step_class and opcode and not opcode.startswith(step_class + '.') and opcode not in ('shekina.invoke',):
                    # Componer 'shekina.init' desde class=shekina, opcode=init (si no viene calificado ya)
                    opcode = f"{step_class}.{opcode}"
                is_alias = False
                if opcode == 'shekina.invoke':
                    # Ejecutar una tarea interna por nombre (en 'step' o 'task')
                    target_task = s.get('task') or s.get('step')
                    payload['_caller_step'] = s.get('step')
                    is_alias = isinstance(target_task, str) and 'alias' in target_task.lower()
                    res = self._invoke_task(target_task, context=context, payload=payload)
                elif isinstance(opcode, str) and opcode.startswith('shekina.'):
                    # OpCodes internos como 'shekina.init', 'shekina.transmute', etc.
                    payload['_caller_step'] = s.get('step')
                    is_alias = 'alias' in opcode
                    res = self._invoke_task(opcode, context=context, payload=payload)
                elif isinstance(opcode, str) and opcode.startswith('alchemist.'):
                    # Permitir dispatch interno simple para alchemist.* si no hay registry
                    res = self._invoke_task(opcode, context=context, payload=payload)
                else:
                    fn = reg.resolve(opcode) if opcode else None
                    if fn is None:
                        run_log.append({'id': s['id'], 'step': s['step'], 'status': 'unknown-opcode'})
                        continue
                    res = fn(context, payload)
                if s.get('outputs'):
                    out0 = s['outputs'][0]
                    if isinstance(res, dict) and out0 not in context:
                        if is_alias and 'value' in res and len(res) == 1:
                            context[out0] = res['value']
                        else:
                            context[out0] = res
                run_log.append({'id': s['id'], 'step': s['step'], 'status': 'ok'})
        return context, run_log

    def _compile_levels(self, table: List[Dict[str, Any]]) -> Tuple[List[List[str]], Dict[str, Dict[str, Any]]]:
        name_map = {s['step']: s['id'] for s in table}
        from collections import defaultdict, deque
        deps = {s['id']: [name_map.get(d, d) for d in s.get('depends_on', [])] for s in table}
        rev = defaultdict(list)
        indeg = {k: 0 for k in deps}
        for k, ds in deps.items():
            for d in ds:
                rev[d].append(k)
                indeg[k] += 1
        q = deque([k for k, v in indeg.items() if v == 0])
        order: List[str] = []
        while q:
            u = q.popleft()
            order.append(u)
            for v in rev[u]:
                indeg[v] -= 1
                if indeg[v] == 0:
                    q.append(v)
        # agrupar en niveles
        levels: List[List[str]] = []
        level_set = set([k for k, v in deps.items() if len(v) == 0])
        used = set()
        while level_set:
            levels.append(list(level_set))
            used |= level_set
            next_set = set()
            for u in level_set:
                for v in rev[u]:
                    if v in used:
                        continue
                    if all(d in used for d in deps[v]):
                        next_set.add(v)
            level_set = next_set
        return levels, {s['id']: s for s in table}

    @staticmethod
    def _eval_condition(cond: Optional[Dict[str, Any]]) -> bool:
        if not cond:
            return True
        if isinstance(cond, dict) and '==' in cond:
            a, b = cond['==']
            return a == b
        return True

    # --- Invoke simple: tareas internas de alto nivel ---
    def _invoke_task(self, task_name: Optional[str], context: Dict[str, Any], payload: Dict[str, Any]):
        """Ejecuta tareas internas simples por nombre.

        Ejemplos:
        - 'shekina.transmute_*': ejecuta AlchemistPrime con df_data/df_flow/df_dict.
        - 'shekina.upsert_dataGraph': pobla DaathGraph con df y configuraciones.
        - 'shekina.compile_alchemist_flow': compila df_flow desde la tabla única (filtrada por process_key).
        """
        if not task_name:
            return {}
        lname = task_name.lower()
        # Tarea de fin/no-op para marcar cierre de subproceso
        if lname.endswith('.end') or lname == 'end' or lname == 'shekina.end':
            return {'end': True}
        # Compilar df_flow desde la tabla unificada (filas con opcode == 'alchemist.step')
        if 'compile_alchemist_flow' in lname:
            from aleya.flow_utils import compile_alchemist_flow as _caf
            table = self.process_table or getattr(self, '_current_table', None) or []
            dd_in = payload.get('inputs') or {}
            if isinstance(dd_in, dict):
                # Aceptar business_process con doble s también
                flt_pk = dd_in.get('process_key') or dd_in.get('processKey') or dd_in.get('business_process') or dd_in.get('bussiness_process')
            else:
                flt_pk = None
            # Resolver referencias si son templates o paths de contexto
            if isinstance(flt_pk, str):
                flt_pk = self._resolve_references(flt_pk, context)
            return _caf(table, filter_process_key=flt_pk)
        # Compilación genérica de grupos de tareas (agnóstica del backend)
        if 'compile_task_group' in lname:
            dd_in = payload.get('inputs') or {}
            table = self.process_table or getattr(self, '_current_table', None) or []
            # Clave de filtro del grupo
            key = None
            if isinstance(dd_in, dict):
                key = dd_in.get('process_key') or dd_in.get('processKey') or dd_in.get('business_process') or dd_in.get('bussiness_process')
            if isinstance(key, str):
                key = self._resolve_references(key, context)
            # Selección desde fuente externa (DataFrame en contexto) o desde process_table
            src_path = None
            where_expr = None
            executor_override = None
            class_lock = None
            if isinstance(dd_in, dict):
                src_path = dd_in.get('from') or dd_in.get('source')
                where_expr = dd_in.get('where') or dd_in.get('filter')
                executor_override = dd_in.get('executor')
                class_lock = dd_in.get('class_lock')
                # Soporte DSL: select * from <path> where <expr>
                dsl = dd_in.get('dsl')
                if isinstance(dsl, str):
                    msel = re.match(r"(?is)^\s*select\s+\*\s+from\s+([A-Za-z0-9_.]+)(?:\s+where\s+(.+))?\s*$", dsl)
                    if msel:
                        src_path = src_path or msel.group(1)
                        if not where_expr and msel.group(2):
                            where_expr = msel.group(2)
            executor_override = dd_in.get('executor') if isinstance(dd_in, dict) else None
            class_lock = dd_in.get('class_lock') if isinstance(dd_in, dict) else None
            if class_lock is None:
                class_lock = True
            # Aliases de ejecutor desde config global (evita romper tablas antiguas)
            exec_aliases = {}
            try:
                exec_aliases = (self.config or {}).get('executor_aliases') or {}
            except Exception:
                exec_aliases = {}
            # Caso A: fuente es un DF en contexto
            if isinstance(src_path, str):
                df = self._resolve_references(src_path, context)
                if df is None and src_path == 'df_flow':
                    df = self._get_from_context(context, 'alchemist.flow.df_flow')
                if df is None:
                    return {'error': f"Fuente '{src_path}' no encontrada en contexto."}
                df_sel = df
                if isinstance(where_expr, str) and where_expr.strip():
                    try:
                        df_sel = self._apply_where_to_df(df, where_expr, context)
                    except Exception as ex:
                        return {'error': f"Error aplicando where: {ex}"}
                # Determinar ejecutor
                exec_name = executor_override
                try:
                    import pandas as _pd  # noqa: F401
                    cols = list(getattr(df_sel, 'columns', []))
                    if exec_name is None:
                        if 'class' in cols:
                            uniq = set([str(x) for x in df_sel['class'].dropna().unique().tolist()])
                            if len(uniq) == 1:
                                exec_name = list(uniq)[0]
                        if exec_name is None and 'opcode' in cols:
                            # derivar prefijo class de 'class.op'
                            op_series = df_sel['opcode'].dropna().astype(str)
                            prefixes = set([s.split('.')[0] for s in op_series if '.' in s])
                            if len(prefixes) == 1:
                                exec_name = list(prefixes)[0]
                except Exception:
                    pass
                # Mapear alias si aplica
                if isinstance(exec_name, str) and exec_name in exec_aliases:
                    exec_name = exec_aliases[exec_name]
                if class_lock and (not exec_name):
                    return {'error': 'No se pudo determinar un ejecutor único para el grupo (class_lock=True). Especifique inputs.executor.'}
                items = df_sel.to_dict(orient='records') if hasattr(df_sel, 'to_dict') else []
                return {'task_group': {'executor': exec_name, 'items': items, 'count': len(items)}}
            # Caso B: usar process_table y filtrar por clave del grupo
            if not key:
                return {'error': 'Falta process_key/business_process para compilar el grupo (o defina inputs.from).'}
            rows = [r for r in (table or []) if r.get('process_key') == key]
            if not rows:
                return {'error': f"No hay filas para la clave '{key}'."}
            # Determinar clases involucradas
            classes_raw = set([str(r.get('class') or '').strip() for r in rows if r.get('class')])
            # Intentar derivar por opcode prefijado si no hay 'class'
            if not classes_raw and any(isinstance(r.get('opcode'), str) and '.' in r.get('opcode') for r in rows):
                classes_raw = set([r['opcode'].split('.')[0] for r in rows if isinstance(r.get('opcode'), str) and '.' in r.get('opcode')])
            # Aplicar alias de ejecutor a las clases detectadas
            classes = set([exec_aliases.get(c, c) for c in classes_raw])
            if not classes and any(isinstance(r.get('opcode'), str) and '.' in r.get('opcode') for r in rows):
                op_classes = set([r['opcode'].split('.')[0] for r in rows if isinstance(r.get('opcode'), str) and '.' in r.get('opcode')])
                classes |= set([exec_aliases.get(c, c) for c in op_classes])
            exec_name = executor_override or (list(classes)[0] if len(classes) == 1 else None)
            if isinstance(exec_name, str) and exec_name in exec_aliases:
                exec_name = exec_aliases[exec_name]
            if class_lock and (exec_name is None):
                return {'error': f"Se encontraron múltiples clases en el grupo '{key}': {sorted(list(classes))}. Establezca inputs.executor o unifique la clase."}
            # Caso especial: si es alchemist y las filas son alchemist.step, producir también df_flow
            out: Dict[str, Any] = {'task_group': {'executor': exec_name, 'items': rows, 'count': len(rows)}}
            try:
                if exec_name == 'alchemist' and any(r.get('opcode') == 'alchemist.step' for r in rows):
                    from aleya.flow_utils import compile_alchemist_flow as _caf
                    out.update(_caf(table, filter_process_key=key))
            except Exception:
                pass
            return out
        # Ejecución de grupo de tareas compilado (MVP: soporte 'alchemist')
        if 'execute_task_group' in lname:
            dd_in = payload.get('inputs') or {}
            # Pre-carga de config de ejecutores y aliases para decidir estrategia temprana
            try:
                exec_aliases_pre = (self.config or {}).get('executor_aliases') or {}
                class_cfg_pre = getattr(self, '_class_config', None)
                if class_cfg_pre is None:
                    cfg_path = (self.config or {}).get('class_config_path') or os.path.join(os.path.dirname(__file__), 'config-class.json')
                    if os.path.exists(cfg_path):
                        with open(cfg_path, 'r', encoding='utf-8') as fh:
                            class_cfg_pre = json.load(fh)
                            self._class_config = class_cfg_pre
                if isinstance(class_cfg_pre, dict):
                    more_aliases = class_cfg_pre.get('executor_aliases') or {}
                    if more_aliases:
                        exec_aliases_pre = {**more_aliases, **exec_aliases_pre}
            except Exception:
                class_cfg_pre = None
                exec_aliases_pre = {}
            pre_exec = dd_in.get('executor') if isinstance(dd_in, dict) else None
            if isinstance(pre_exec, str) and pre_exec in exec_aliases_pre:
                pre_exec = exec_aliases_pre[pre_exec]
            pre_strategy = None
            if isinstance(class_cfg_pre, dict) and pre_exec:
                pre_strategy = (class_cfg_pre.get('executors') or {}).get(pre_exec, {}).get('strategy')
            if pre_strategy is None and pre_exec:
                pre_strategy = 'internal_alchemist' if pre_exec == 'alchemist' else 'run_rows'
            # Si es internal_daath y no hay clave de grupo ni fuente, ejecutar directo sin compilar
            if pre_strategy == 'internal_daath':
                has_group_key = False
                if isinstance(dd_in, dict) and (dd_in.get('process_key') or dd_in.get('processKey') or dd_in.get('business_process') or dd_in.get('bussiness_process') or dd_in.get('from') or dd_in.get('source')):
                    has_group_key = True
                if not has_group_key:
                    # Reusar la rama existente de internal_daath (copiada aquí para atajo)
                    dd = dd_in
                    cols = dd.get('columns')
                    if cols is None:
                        df_data = self._resolve_references(dd.get('df_data'), context)
                        if df_data is None:
                            df_data = self._get_from_context(context, 'shekina.df_data')
                        try:
                            import pandas as _pd  # noqa: F401
                            if df_data is not None:
                                cols = list(getattr(df_data, 'columns', []))
                        except Exception:
                            cols = None
                    cols = list(cols) if cols is not None else []
                    synonyms_map = dd.get('synonyms_map')
                    canonical_map = dd.get('canonical_map')
                    canonical_set = set(dd.get('canonical_set') or [])
                    col_stats = dd.get('col_stats') or {}
                    auto_upsert = bool(dd.get('auto_upsert', False))
                    # Construir mapping col->canonical
                    col2canon = {}
                    if isinstance(synonyms_map, dict):
                        for k, v in synonyms_map.items():
                            if isinstance(k, str) and isinstance(v, str):
                                col2canon[k] = v
                    if isinstance(canonical_map, dict):
                        for canon, syns in canonical_map.items():
                            if not isinstance(syns, (list, tuple)):
                                continue
                            for s in syns:
                                if isinstance(s, str):
                                    col2canon.setdefault(s, canon)
                    unresolved, conflicts, canon_to_cols = [], [], {}
                    for c in cols:
                        canon = col2canon.get(c)
                        if not canon:
                            unresolved.append(c)
                            continue
                        canon_to_cols.setdefault(canon, []).append(c)
                    for canon, lst in canon_to_cols.items():
                        if len(lst) > 1:
                            def score(col):
                                st = col_stats.get(col, {})
                                pn = float(st.get('percent_numeric', 0))
                                pz = float(st.get('percent_null', 0))
                                return (pn, -pz)
                            chosen = sorted(lst, key=score, reverse=True)[0]
                            rec = f"usar {chosen}"
                            details = {col: col_stats.get(col, {}) for col in lst}
                            conflicts.append({'canonical': canon, 'columns': lst, 'recommendation': rec, 'details': details})
                    status = 'ok'
                    msgs = []
                    if unresolved:
                        status = 'error'; msgs.append(f"Sin sinónimo canónico: {sorted(unresolved)}")
                    if conflicts:
                        status = 'error'
                        for cf in conflicts:
                            msgs.append(f"Conflicto de sinónimos para '{cf['canonical']}': {cf['columns']}")
                    result = {'status_pk': status, 'msg_error': ' | '.join(msgs) if msgs else '', 'unresolved': unresolved, 'conflicts': conflicts, 'trigger': 'upsert__daath__stdCols' if status == 'error' else None}
                    if status == 'error':
                        up_nodes, up_edges = [], []
                        for c in unresolved:
                            up_nodes.append({'uri_id': dd.get('source_domain', 'unknown') + ':' + str(c), 'is_canonical': False, 'properties': col_stats.get(c, {})})
                        for cf in conflicts:
                            canon = cf['canonical']
                            chosen = cf['recommendation'].replace('usar ', '') if isinstance(cf.get('recommendation'), str) else None
                            for c in cf['columns']:
                                if c == chosen:
                                    continue
                                up_edges.append({'definition': f"{dd.get('source_domain', 'unknown')}:{c}--|ES_SINONIMO_DE|->{canon}", 'properties': cf.get('details', {}).get(c, {})})
                        result['upsert_plan'] = {'nodes': up_nodes, 'edges': up_edges}
                        if auto_upsert and (up_nodes or up_edges):
                            try:
                                if self.daath is None:
                                    self.init_daath()
                                result['auto_upsert_scheduled'] = True
                            except Exception as ex:
                                result['auto_upsert_error'] = str(ex)
                    return result
            # 1) Compilar el grupo con las mismas inputs
            comp_res = self._invoke_task('shekina.compile_task_group', context=context, payload={'inputs': dd_in})
            if isinstance(comp_res, dict) and 'error' in comp_res:
                return comp_res
            group = (comp_res or {}).get('task_group') or {}
            executor = group.get('executor')
            if not executor:
                return {'error': 'No se pudo determinar el ejecutor del grupo.'}
            # Normalizar por aliases del ejecutor
            try:
                # fusionar aliases: config local y config-class.json si existe
                exec_aliases = (self.config or {}).get('executor_aliases') or {}
                class_cfg = getattr(self, '_class_config', None)
                if class_cfg is None:
                    # intentar cargar config-class.json por convención
                    cfg_path = (self.config or {}).get('class_config_path') or os.path.join(os.path.dirname(__file__), 'config-class.json')
                    try:
                        if os.path.exists(cfg_path):
                            with open(cfg_path, 'r', encoding='utf-8') as fh:
                                class_cfg = json.load(fh)
                                self._class_config = class_cfg
                    except Exception:
                        class_cfg = None
                if isinstance(class_cfg, dict):
                    more_aliases = class_cfg.get('executor_aliases') or {}
                    if more_aliases:
                        exec_aliases = {**more_aliases, **exec_aliases}
            except Exception:
                exec_aliases = {}
            if isinstance(executor, str) and executor in exec_aliases:
                executor = exec_aliases[executor]
            # 2) Estrategia por ejecutor desde config-class.json (fallbacks sensatos)
            strategy = None
            if isinstance(class_cfg, dict):
                strategy = (class_cfg.get('executors') or {}).get(executor, {}).get('strategy')
            # Fallback por defecto: alchemist -> internal_alchemist; otros -> run_rows
            if strategy is None:
                strategy = 'internal_alchemist' if executor == 'alchemist' else 'run_rows'

            # 3) Despachar según estrategia/ejecutor
            if strategy == 'internal_daath':
                # Validación y orquestación mínima para homología basada en grafo (sin llamar registry)
                dd = dd_in if isinstance(dd_in, dict) else {}
                # Entradas: columns (lista) o df_data (tomamos columnas), mapeos de sinónimos
                cols = dd.get('columns')
                if cols is None:
                    # intentar derivar de df_data en inputs o contexto
                    df_data = self._resolve_references(dd.get('df_data'), context)
                    if df_data is None:
                        df_data = self._get_from_context(context, 'shekina.df_data')
                    try:
                        import pandas as _pd  # noqa: F401
                        if df_data is not None:
                            cols = list(getattr(df_data, 'columns', []))
                    except Exception:
                        cols = None
                cols = list(cols) if cols is not None else []
                synonyms_map = dd.get('synonyms_map')  # col -> canonical
                canonical_map = dd.get('canonical_map')  # canonical -> [synonyms]
                canonical_set = set(dd.get('canonical_set') or [])
                col_stats = dd.get('col_stats') or {}  # opcional: {col: {percent_numeric, percent_null}}
                strict = bool(dd.get('strict', True))
                auto_upsert = bool(dd.get('auto_upsert', False))

                # Construir mapping col->canonical
                col2canon = {}
                if isinstance(synonyms_map, dict):
                    for k, v in synonyms_map.items():
                        if isinstance(k, str) and isinstance(v, str):
                            col2canon[k] = v
                if isinstance(canonical_map, dict):
                    for canon, syns in canonical_map.items():
                        if not isinstance(syns, (list, tuple)):
                            continue
                        for s in syns:
                            if isinstance(s, str):
                                col2canon.setdefault(s, canon)

                unresolved = []
                conflicts = []
                canon_to_cols = {}
                for c in cols:
                    canon = col2canon.get(c)
                    if not canon:
                        unresolved.append(c)
                        continue
                    lst = canon_to_cols.setdefault(canon, [])
                    lst.append(c)

                # Detectar conflictos (más de una col hacia el mismo canonical)
                for canon, lst in canon_to_cols.items():
                    if len(lst) > 1:
                        # Heurística simple de recomendación usando col_stats
                        def score(col):
                            st = col_stats.get(col, {})
                            pn = float(st.get('percent_numeric', 0))
                            pz = float(st.get('percent_null', 0))
                            return (pn, -pz)
                        chosen = sorted(lst, key=score, reverse=True)[0]
                        rec = f"usar {chosen}"
                        details = {col: col_stats.get(col, {}) for col in lst}
                        conflicts.append({
                            'canonical': canon,
                            'columns': lst,
                            'recommendation': rec,
                            'details': details,
                        })

                status = 'ok'
                msgs = []
                if unresolved:
                    status = 'error'
                    msgs.append(f"Sin sinónimo canónico: {sorted(unresolved)}")
                if conflicts:
                    status = 'error'
                    for cf in conflicts:
                        msgs.append(f"Conflicto de sinónimos para '{cf['canonical']}': {cf['columns']}")

                result = {
                    'status_pk': status,
                    'msg_error': ' | '.join(msgs) if msgs else '',
                    'unresolved': unresolved,
                    'conflicts': conflicts,
                    'trigger': 'upsert__daath__stdCols' if status == 'error' else None
                }

                # Plan de upsert (no ejecuta por defecto): nodos y relaciones a sugerir
                if status == 'error':
                    up_nodes = []
                    up_edges = []
                    # Nodos para columnas no mapeadas
                    for c in unresolved:
                        up_nodes.append({
                            'uri_id': dd.get('source_domain', 'unknown') + ':' + str(c),
                            'is_canonical': False,
                            'properties': col_stats.get(c, {})
                        })
                    # Relaciones ES_SINONIMO_DE para conflictos (elegida como recomendación)
                    for cf in conflicts:
                        canon = cf['canonical']
                        chosen = cf['recommendation'].replace('usar ', '') if isinstance(cf.get('recommendation'), str) else None
                        for c in cf['columns']:
                            if c == chosen:
                                continue
                            up_edges.append({
                                'definition': f"{dd.get('source_domain', 'unknown')}:{c}--|ES_SINONIMO_DE|->{canon}",
                                'properties': cf.get('details', {}).get(c, {})
                            })
                    result['upsert_plan'] = {'nodes': up_nodes, 'edges': up_edges}

                    # Auto-upsert opcional si Daath está disponible
                    if auto_upsert and (up_nodes or up_edges):
                        try:
                            if self.daath is None:
                                self.init_daath()
                            # Se expone un plan; la ejecución real de grafo es específica del proyecto
                            # Aquí solo devolvemos el plan y marcamos intención
                            result['auto_upsert_scheduled'] = True
                        except Exception as ex:
                            result['auto_upsert_error'] = str(ex)
                return result
            if strategy == 'run_rows':
                # Ejecuta directamente las filas del grupo con el registry, respetando depends_on
                items = group.get('items') or []
                try:
                    child = Shekina(self.config, process_table=self.process_table)
                    child.set_registry(self.registry)
                    ctx_child, log_child = child.run_process_table(items, registry=self.registry, process_key=None, initial_context=context)
                    # Propagar resultados relevantes al contexto actual (shallow merge)
                    try:
                        context.update({k: v for k, v in ctx_child.items() if k not in ('shekina',)})
                        if isinstance(ctx_child.get('shekina'), dict):
                            context.setdefault('shekina', {}).update(ctx_child['shekina'])
                    except Exception:
                        pass
                    return {'executed': True, 'run_log': log_child, 'items': len(items)}
                except Exception as ex:
                    return {'error': f"execute_task_group({executor}) falló ejecutando filas: {ex}"}
            if executor == 'alchemist':
                # Resolver df_flow/df_data/df_dict desde compile, inputs o contexto
                flow = comp_res.get('df_flow')
                if flow is None:
                    flow = self._resolve_references(dd_in.get('df_flow'), context)
                    if flow is None:
                        flow = self._get_from_context(context, 'alchemist.flow.df_flow')
                data = self._resolve_references(dd_in.get('df_data'), context) if isinstance(dd_in, dict) else None
                if data is None:
                    data = self._get_from_context(context, 'shekina.df_data') or self._get_from_context(context, 'mirror.select.df_data')
                dicc = self._resolve_references(dd_in.get('df_dict'), context) if isinstance(dd_in, dict) else None
                if dicc is None:
                    dicc = self._get_from_context(context, 'shekina.df_dict') or self._get_from_context(context, 'mirror.select.df_dict')
                if flow is None:
                    return {'error': 'execute_task_group(alchemist): falta df_flow (proporcione inputs.df_flow o compile desde process_table).'}
                if data is None:
                    return {'error': 'execute_task_group(alchemist): falta df_data (proporcione inputs.df_data o pueble context.shekina.df_data).'}
                try:
                    from alchemist.alchemist_prime import AlchemistPrime as _AP
                    ap = _AP(data_df=data, config_df=flow, dictionary_df=dicc)
                    ap.transmute().agregar_status_y_errores().limpiar_columnas_intermedias()
                    out_df = ap.to_pandas()
                    # Persistir en contexto útil
                    self._set_in_context(context, 'alchemist.last_run.df_result', out_df)
                    self._set_in_context(context, 'alchemist.last_run.df_flow', flow)
                    return {'df_data_transmuted': out_df, 'ap': ap}
                except Exception as ex:
                    return {'error': f"execute_task_group(alchemist) falló: {ex}"}
            # Ejecutores no soportados aún
            return {'error': f"execute_task_group: ejecutor '{executor}' no soportado aún."}
        # Transmutación
        if 'transmute' in lname:
            # 1) Si existe instancia previa en contexto, úsala para evitar re-instanciación y duplicación
            inst = context.get('shekina.alchemist') or context.get('alchemist')
            if isinstance(inst, dict) and 'ap' in inst:
                ap = inst['ap']
                try:
                    ap.transmute().agregar_status_y_errores().limpiar_columnas_intermedias()
                    return {'df_data_transmuted': ap.to_pandas()}
                except Exception as ex:
                    return {'error': f'Transmute con instancia falló: {ex}'}
            # 2) Si no hay instancia guardada, construir una rápida desde inputs/context (sin copiar frames)
            dd = payload.get('inputs') or {}
            data = dd.get('df_data') or context.get('shekina', {}).get('df_data') or context.get('mirror.select', {}).get('df_data')
            flow = dd.get('df_flow') or context.get('alchemist.flow', {}).get('df_flow')
            dicc = dd.get('df_dict') or context.get('shekina', {}).get('df_dict') or context.get('mirror.select', {}).get('df_dict')
            if data is None or flow is None:
                return {'error': 'Faltan df_data/df_flow para transmutar.'}
            try:
                from alchemist.alchemist_prime import AlchemistPrime as _AP
                ap = _AP(data_df=data, config_df=flow, dictionary_df=dicc)
                ap.transmute().agregar_status_y_errores().limpiar_columnas_intermedias()
                return {'df_data_transmuted': ap.to_pandas()}
            except Exception as ex:
                return {'error': f'Transmute falló: {ex}'}
        # Upsert de grafo
        if 'upsert_datagraph' in lname or 'upsert_daath' in lname:
            nodes_cfg = payload.get('nodes_config')
            edges_cfg = payload.get('edges_config')
            df = payload.get('df_data')
            if self.daath is None:
                self.init_daath()
            if df is not None and nodes_cfg and edges_cfg:
                try:
                    import pandas as pd
                    if not isinstance(df, pd.DataFrame):
                        return {'error': 'df_data debe ser un DataFrame de pandas'}
                    self.daath.populate_from_data(df, nodes_cfg, edges_cfg)
                    return {'graph_updated': True}
                except Exception as ex:
                    return {'error': f'Error poblando grafo: {ex}'}
            return {'error': 'Faltan df_data/nodes_config/edges_config para upsert grafo.'}
        if 'alchemist.init' in lname or 'shekina.alchemist.init' in lname:
            # Inicializa y guarda instancia de AlchemistPrime referenciando data/flow/dict sin duplicar memoria
            dd = payload.get('inputs') or {}
            data = self._resolve_references(dd.get('df_data'), context)
            if isinstance(data, str) and data.startswith('context.'):
                data = self._resolve_references(data, context)
            if data is None:
                data = context.get('shekina', {}).get('df_data')
            flow = self._resolve_references(dd.get('df_flow'), context) or context.get('alchemist.flow', {}).get('df_flow')
            dicc = self._resolve_references(dd.get('df_dict'), context) or context.get('shekina', {}).get('df_dict')
            try:
                from alchemist.alchemist_prime import AlchemistPrime as _AP
                ap = _AP(data_df=data, config_df=flow, dictionary_df=dicc)
                return {'ap': ap, 'df_data': data, 'df_flow': flow, 'df_dict': dicc}
            except Exception as ex:
                return {'error': f'Init de Alchemist falló: {ex}'}
        if 'for_each' in lname:
            # Iterador genérico: soporta DSL en inputs.dsl y overrides (periodo_inicio/fin, process_key) y/o iteración por tabla
            inputs_cfg = payload.get('inputs') or {}
            dsl = inputs_cfg.get('dsl')
            # Derivar periodos
            pini = inputs_cfg.get('periodo_inicio')
            pfin = inputs_cfg.get('periodo_fin')
            pk_override = inputs_cfg.get('process_key') or inputs_cfg.get('processKey')
            # Modo de ejecución: sequential (default) | parallel (acepta legacy 'parallel': true)
            exec_mode = payload.get('exec_mode') or inputs_cfg.get('exec_mode')
            if exec_mode is None:
                par_flag = payload.get('parallel') or inputs_cfg.get('parallel') or context.get('shekina', {}).get('parallel') or False
                exec_mode = 'parallel' if par_flag else 'sequential'
            periodos: List[str] = []
            iter_values_from_table: Optional[List[Any]] = None
            iter_var: Optional[str] = None
            where_clause: Optional[str] = None
            if isinstance(dsl, str):
                # period in (a,b,...) o period in (a..b)
                m = re.search(r"(?i)\bperiod(?:o)?\s+in\s*\(([^)]+)\)", dsl)
                if m:
                    body = m.group(1).strip()
                    if '..' in body:
                        a, b = [t.strip().strip("'\"") for t in body.split('..', 1)]
                        pini, pfin = a, b
                    else:
                        vals = [t.strip().strip("'\"") for t in body.split(',') if t.strip()]
                        periodos = vals
                # process_key = 'xxx'
                m2 = re.search(r"(?i)\bprocess_key\s*=\s*'([^']+)'", dsl)
                if m2:
                    pk_override = m2.group(1)
                # var in <tablePath> [where ...]
                mtab = re.search(r"(?i)^\s*([A-Za-z_][\w]*)\s+in\s+([A-Za-z0-9_.]+)(?:\s+where\s+(.+))?\s*$", dsl)
                if mtab:
                    iter_var = mtab.group(1)
                    table_path = mtab.group(2)
                    where_clause = mtab.group(3)
                    table_iter = self._resolve_references(table_path, context)
                    if table_iter is None and table_path == 'df_flow':
                        table_iter = self._get_from_context(context, 'alchemist.flow.df_flow')
                    try:
                        import pandas as pd  # noqa: F401
                        df = table_iter
                        if where_clause:
                            df = self._apply_where_to_df(df, where_clause, context)
                        if iter_var in getattr(df, 'columns', []):
                            # Guardar df e iter_var para scheduling por niveles si hay depends_on
                            self._iter_df = df
                            self._iter_iter_var = iter_var
                            items_series = df[iter_var]
                            iter_values_from_table = list(items_series.dropna().astype(str).unique())
                        elif iter_var == 'row':
                            iter_values_from_table = list(range(len(df)))
                    except Exception:
                        iter_values_from_table = None
            # Resolver referencias si son strings
            if isinstance(pini, str):
                pini = self._resolve_references(pini, context)
            if isinstance(pfin, str):
                pfin = self._resolve_references(pfin, context)
            # Construir periodos desde rango si aplica
            if not periodos:
                if pini and pfin:
                    try:
                        periodos = self._expand_period_range(str(pini), str(pfin))
                    except Exception:
                        periodos = []
                else:
                    periodos = context.get('shekina', {}).get('periodos') or context.get('periodos') or []
            # Si viene iterador por tabla, usarlo en lugar de periodos
            table_items = None
            if iter_values_from_table is not None:
                table_items = iter_values_from_table
                periodos = []
            if not periodos and not pk_override and not table_items:
                return {'error': 'No hay periodos, tabla a iterar ni process_key definidos (use inputs.dsl o periodo_inicio/fin o process_key).'}
            # Opciones de payload: process_key_template, steps_subset
            pk_tmpl = payload.get('process_key_template') or '%(periodo)s'
            steps_subset = payload.get('steps')  # opcional: lista de step names a ejecutar
            do_parallel = (str(exec_mode).lower() == 'parallel')
            # Flags de dependencias
            strict_deps = payload.get('strict_dependencies')
            if strict_deps is None:
                strict_deps = inputs_cfg.get('strict_dependencies', False)
            allow_external = payload.get('allow_external_deps')
            if allow_external is None:
                allow_external = inputs_cfg.get('allow_external_deps', True)
            results: List[Dict[str, Any]] = []
            iter_vals = periodos if periodos else (table_items if table_items is not None else [None])

            def _build_child(item):
                per = item if table_items is None else None
                # Override por item si iteramos una columna llamada process_key
                pk_override_item = None
                if table_items is not None and isinstance(iter_var, str) and iter_var.lower() == 'process_key':
                    pk_override_item = str(item)
                table_cur = self._current_table or self.process_table or []
                # Si se overridea process_key, usar la tabla completa para que el hijo filtre correctamente
                base_table = (self.process_table or table_cur) if (pk_override or pk_override_item) else table_cur
                sub = [r for r in base_table if r.get('step') in steps_subset] if steps_subset else list(base_table)
                # Inyectar variables en contexto base para la corrida hija
                child_context = dict(context)
                if per is not None:
                    child_context['periodo'] = per
                if 'shekina' in child_context and isinstance(child_context['shekina'], dict):
                    if per is not None:
                        child_context['shekina']['current_periodo'] = per
                else:
                    child_context['shekina'] = ({'current_periodo': per} if per is not None else {})
                # exponer variable iter_var
                if isinstance(iter_var, str) and iter_var and table_items is not None:
                    try:
                        self._set_in_context(child_context, iter_var, item)
                    except Exception:
                        pass
                # scope por step que invoca (para anidados): context.<caller_step>.current_periodo
                caller = payload.get('_caller_step')
                if isinstance(caller, str) and caller:
                    try:
                        self._set_in_context(child_context, f"{caller}.current_periodo", per)
                    except Exception:
                        pass
                child_pk = pk_override_item or pk_override or self._current_process_key
                return sub, child_context, child_pk, per, item

            if do_parallel:
                from concurrent.futures import ThreadPoolExecutor, as_completed
                max_workers = payload.get('max_workers') or inputs_cfg.get('max_workers') or None
                futures = []
                with ThreadPoolExecutor(max_workers=max_workers) as ex:
                    # Si hay iteración por tabla y columna depends_on, ejecutar por niveles (olas) de independencia
                    iter_df = getattr(self, '_iter_df', None) if table_items is not None else None
                    iter_col = getattr(self, '_iter_iter_var', None) if table_items is not None else None
                    if iter_df is not None and iter_col and 'depends_on' in getattr(iter_df, 'columns', []):
                        # Construir DAG de dependencias a nivel de valores de iter_col
                        items = [str(x) for x in iter_vals]
                        item_set = set(items)
                        # map item -> deps (intersectados con el universo)
                        def to_list(val):
                            if val is None:
                                return []
                            if isinstance(val, (list, tuple, set)):
                                return list(val)
                            s = str(val).strip()
                            if s == '' or s.lower() in ('none', 'null', 'nan'):
                                return []
                            # intentar JSON
                            try:
                                if s.startswith('[') and s.endswith(']'):
                                    return json.loads(s)
                            except Exception:
                                pass
                            # fallback: split por coma
                            parts = [p.strip().strip("'\"") for p in s.split(',')]
                            return [p for p in parts if p]
                        deps_map = {k: set() for k in items}
                        # agrupar por item y unir depends_on
                        for _, row in iter_df.iterrows():
                            key = str(row.get(iter_col))
                            if key not in deps_map:
                                continue
                            deps_raw = to_list(row.get('depends_on'))
                            deps_map[key] |= {str(d) for d in deps_raw}
                        # Validar dependencias externas
                        if not allow_external:
                            externals = {k: [d for d in v if d not in item_set] for k, v in deps_map.items()}
                            externals = {k: v for k, v in externals.items() if v}
                            if externals:
                                return {'error': 'Dependencias externas no permitidas', 'details': externals}
                        # Si se permiten externas, intersectar con items existentes
                        for k in list(deps_map.keys()):
                            deps_map[k] = set([d for d in deps_map[k] if d in item_set])
                        # Kahn por niveles (usando util compartida)
                        from aleya.flow_utils import build_dependency_waves
                        waves = build_dependency_waves(
                            deps_map,
                            universe=item_set,
                            allow_external_deps=allow_external,
                            strict_dependencies=strict_deps,
                        )
                        if 'error' in waves:
                            return waves
                        levels = waves.get('levels', [])
                        # Ejecutar por olas
                        for wave in levels:
                            futures = []
                            for item in wave:
                                sub, child_context, child_pk, per, item_val = _build_child(item)
                                def _run_one(sub=sub, child_context=child_context, child_pk=child_pk, item_val=item_val, per=per):
                                    try:
                                        child = Shekina(self.config, process_table=self.process_table)
                                        child.set_registry(self.registry)
                                        ctx_child, log_child = child.run_process_table(sub, registry=self.registry, process_key=child_pk, initial_context=child_context)
                                        return {'item': item_val if table_items is not None else per, 'run_log': log_child}
                                    except Exception as ex2:
                                        return {'item': item_val if table_items is not None else per, 'error': str(ex2)}
                                futures.append(ex.submit(_run_one))
                            for f in as_completed(futures):
                                results.append(f.result())
                    else:
                        # Paralelismo simple para lista de items sin dependencias declaradas
                        for item in iter_vals:
                            sub, child_context, child_pk, per, item_val = _build_child(item)
                            def _run_one(sub=sub, child_context=child_context, child_pk=child_pk, item_val=item_val, per=per):
                                try:
                                    child = Shekina(self.config, process_table=self.process_table)
                                    child.set_registry(self.registry)
                                    ctx_child, log_child = child.run_process_table(sub, registry=self.registry, process_key=child_pk, initial_context=child_context)
                                    return {'item': item_val if table_items is not None else per, 'run_log': log_child}
                                except Exception as ex2:
                                    return {'item': item_val if table_items is not None else per, 'error': str(ex2)}
                            futures.append(ex.submit(_run_one))
                        for f in as_completed(futures):
                            results.append(f.result())
            else:
                for item in iter_vals:
                    sub, child_context, child_pk, per, item_val = _build_child(item)
                    try:
                        ctx_child, log_child = self.run_process_table(sub, registry=self.registry, process_key=child_pk, initial_context=child_context)
                        results.append({'item': item_val if table_items is not None else per, 'run_log': log_child})
                    except Exception as ex:
                        results.append({'item': item_val if table_items is not None else per, 'error': str(ex)})
            return {'for_each': results}
        if 'alias' in lname:
            # Caso 1: mappings dict: { 'mappings': { 'context.periodos': 'context.shekina.periodos', 'shekina.global_inicio': 'context.shekina.periodo.inicio' } }
            maps = payload.get('mappings') or payload.get('aliases')
            if isinstance(maps, dict):
                applied = {}
                for target, source in maps.items():
                    val = self._resolve_references(source, context)
                    self._set_in_context(context, target, val)
                    applied[target] = val
                return {'applied': applied}
            # Caso 2: simple from->to
            src = payload.get('source') or payload.get('from')
            tgt = payload.get('target') or payload.get('to')
            if src and tgt:
                val = self._resolve_references(src, context)
                self._set_in_context(context, tgt, val)
                return {'applied': {tgt: val}}
            # Caso 3: sólo devolver valor (se puede mapear vía outputs)
            if src:
                val = self._resolve_references(src, context)
                return {'value': val}
            return {'error': 'Alias requiere mappings o (source/from [+ target/to])'}
        if 'init' in lname:
            # Inicializa configuración para df_flow/df_data/df_config aplicando templates de contexto
            cfg = payload.get('config') or payload.get('inputs') or {}
            # Acepta que la config venga anidada bajo 'config', y/o llaves directas
            if 'config' in cfg:
                cfg = cfg['config']
            df_flow = payload.get('df_flow') or (cfg.get('df_flow') if isinstance(cfg, dict) else None) or {}
            df_data = payload.get('df_data') or (cfg.get('df_data') if isinstance(cfg, dict) else None) or {}
            df_config = payload.get('df_config') or (cfg.get('df_config') if isinstance(cfg, dict) else None) or {}
            # Resolver plantillas y referencias de contexto
            def _resolve(v):
                return self._resolve_references(v, context)
            resolved = {
                'config': _resolve(cfg) if isinstance(cfg, dict) else cfg,
                'df_flow': _resolve(df_flow),
                'df_data': _resolve(df_data),
                'df_config': _resolve(df_config),
            }
            # Manejo de periodos: periodo_inicio y periodo_fin (formato YYYYMM) → context.periodos
            inputs_cfg = payload.get('inputs') or {}
            p_ini = inputs_cfg.get('periodo_inicio') or inputs_cfg.get('periodoStart') or inputs_cfg.get('periodStart')
            p_fin = inputs_cfg.get('periodo_fin') or inputs_cfg.get('periodoEnd') or inputs_cfg.get('periodEnd')
            if p_ini and p_fin:
                try:
                    periodos = self._expand_period_range(str(p_ini), str(p_fin))
                    resolved['periodos'] = periodos
                except Exception:
                    resolved['periodos'] = []
            # Guardar también variantes de nombres útiles
            if p_ini:
                self._set_in_context(resolved, 'shekina.periodo_inicio', p_ini)
                self._set_in_context(resolved, 'shekina.periodo.inicio', p_ini)
            if p_fin:
                self._set_in_context(resolved, 'shekina.periodo_fin', p_fin)
                self._set_in_context(resolved, 'shekina.periodo.fin', p_fin)
            # Propagar también los inputs planos a nivel de resultado (p.ej. periodo, parallel)
            for k, v in (inputs_cfg.items() if isinstance(inputs_cfg, dict) else []):
                resolved[k] = v
            # Aliases en init: soporta 'as'|'aliases' como { alias: source } y/o 'assign' DSL list
            alias_map = inputs_cfg.get('as') or inputs_cfg.get('aliases')
            if isinstance(alias_map, dict):
                for target, source in alias_map.items():
                    val = self._resolve_references(source, {'shekina': resolved, **context})
                    self._set_in_context(resolved, target, val)
                    try:
                        self._set_in_context(context, target, val)
                    except Exception:
                        pass
            assign_list = inputs_cfg.get('assign') or inputs_cfg.get('set')
            if isinstance(assign_list, list):
                import re as _re
                pat = _re.compile(r"^\s*([A-Za-z0-9_.]+)\s*=\s*(.*?)\s*(?:AS\s+([A-Za-z0-9_.]+))?\s*$", _re.IGNORECASE)
                for line in assign_list:
                    if not isinstance(line, str):
                        continue
                    m = pat.match(line)
                    if not m:
                        continue
                    lhs, rhs, alias = m.groups()
                    rhs_val = rhs.strip().strip("'\"")
                    # resolver referencias si parecen paths
                    if rhs_val:
                        rhs_res = self._resolve_references(rhs_val, {'shekina': resolved, **context})
                    else:
                        rhs_res = rhs_val
                    self._set_in_context(resolved, lhs, rhs_res)
                    try:
                        self._set_in_context(context, lhs, rhs_res)
                    except Exception:
                        pass
                    if alias:
                        # alias al nivel raíz del resolved
                        self._set_in_context(resolved, alias, rhs_res)
                        try:
                            self._set_in_context(context, alias, rhs_res)
                        except Exception:
                            pass
            return resolved
        # Por defecto: no-op
        return {}

    def _apply_where_to_df(self, df, where_clause: str, context: Dict[str, Any]):
        """Aplica un 'where' simple con soporte para:
        - col == expr (expr admite concatenación con '+' y paths context.*)
        - col in [a,b]
        - index in [1,2,3]
        - OR con '||' entre cláusulas
        """
        try:
            import pandas as pd  # noqa: F401
        except Exception:
            return df
        def _eval_expr(expr: str):
            expr = expr.strip()
            parts = [p.strip() for p in expr.split('+')]
            def ev(p):
                if (p.startswith("'") and p.endswith("'")) or (p.startswith('"') and p.endswith('"')):
                    return p[1:-1]
                return str(self._resolve_references(p, context))
            return ''.join(ev(p) for p in parts)
        def _parse_list(lst: str):
            inner = lst.strip().strip('[]').strip()
            if not inner:
                return []
            items = [t.strip() for t in inner.split(',')]
            vals = []
            for it in items:
                if (it.startswith("'") and it.endswith("'")) or (it.startswith('"') and it.endswith('"')):
                    vals.append(it[1:-1])
                else:
                    r = self._resolve_references(it, context)
                    vals.append(str(r))
            return vals
        clauses = [c.strip() for c in str(where_clause).split('||')]
        mask_total = None
        for cl in clauses:
            mi = re.match(r"^index\s+in\s*(\[.*\])$", cl, flags=re.IGNORECASE)
            if mi:
                idx_list = _parse_list(mi.group(1))
                try:
                    idx_list = [int(x) for x in idx_list]
                    mask = df.index.isin(idx_list)
                except Exception:
                    mask = None
            else:
                m_in = re.match(r"^([A-Za-z_][\w.]*)\s+in\s*(\[.*\])$", cl)
                if m_in:
                    col = m_in.group(1)
                    lst = _parse_list(m_in.group(2))
                    mask = df[col].astype(str).isin([str(v) for v in lst])
                else:
                    meq = re.match(r"^([A-Za-z_][\w.]*)\s*==\s*(.+)$", cl)
                    if meq:
                        col = meq.group(1)
                        val = _eval_expr(meq.group(2))
                        try:
                            mask = (df[col] == val)
                        except Exception:
                            mask = None
                    else:
                        mask = None
            if mask is not None:
                mask_total = mask if mask_total is None else (mask_total | mask)
        if mask_total is not None:
            try:
                return df[mask_total]
            except Exception:
                return df
        return df

    @staticmethod
    def _get_from_context(ctx: Dict[str, Any], path: str):
        """Obtiene un valor de contexto usando path con puntos, p.ej. 'shekina.df_data.query'."""
        cur: Any = ctx
        for part in path.split('.'):
            if isinstance(cur, dict):
                cur = cur.get(part)
            else:
                try:
                    cur = getattr(cur, part)
                except Exception:
                    return None
        return cur

    def _resolve_references(self, value: Any, context: Dict[str, Any]):
        """Resuelve strings como 'context.x.y', templates '%%context.something%%',
        o paths sin prefijo (p.ej. s0__mes_ini o shekina.periodo.inicio) dentro de dicts/listas."""
        if isinstance(value, str):
            s = value
            # Caso 1: path directo 'context.xxx.yyy'
            if s.startswith('context.'):
                return self._get_from_context(context, s[len('context.'):])
            # Caso 2: templates %%context.xxx%% (pueden haber múltiples en el string)
            def repl(m):
                inner = m.group(1).strip()
                if inner.startswith('context.'):
                    v = self._get_from_context(context, inner[len('context.'):])
                    return '' if v is None else str(v)
                # legacy: context.get_xxx
                if inner.startswith('context.get_'):
                    key = inner[len('context.get_'):]
                    v = context.get(key)
                    return '' if v is None else str(v)
                return m.group(0)
            s2 = re.sub(r"%%([^%]+)%%", repl, s)
            if s2 != s:
                return s2
            # Caso 3: path sin prefijo
            if re.match(r'^[A-Za-z_][A-Za-z0-9_.]*$', s):
                v = self._get_from_context(context, s)
                if v is not None:
                    return v
                # fallback a namespace shekina
                v2 = self._get_from_context(context, f"shekina.{s}")
                if v2 is not None:
                    return v2
            return s
        if isinstance(value, list):
            return [self._resolve_references(v, context) for v in value]
        if isinstance(value, dict):
            return {k: self._resolve_references(v, context) for k, v in value.items()}
        return value

    @staticmethod
    def _set_in_context(ctx: Dict[str, Any], path: str, value: Any):
        """Setea un valor en el contexto usando path con puntos (crea dicts intermedios si faltan).
        Admite paths que comienzan con 'context.' y serán normalizados.
        """
        p = path
        if p.startswith('context.'):
            p = p[len('context.'):]
        parts = p.split('.') if p else []
        cur = ctx
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                cur[part] = value
            else:
                nxt = cur.get(part)
                if not isinstance(nxt, dict):
                    nxt = {}
                    cur[part] = nxt
                cur = nxt
        return ctx

    @staticmethod
    def _expand_period_range(p_ini: str, p_fin: str) -> List[str]:
        """Expande un rango YYYYMM inclusivo en una lista de periodos ordenados."""
        def parse(p):
            y = int(p[:4]); m = int(p[4:6])
            return y, m
        y1, m1 = parse(p_ini)
        y2, m2 = parse(p_fin)
        vals = []
        y, m = y1, m1
        while (y < y2) or (y == y2 and m <= m2):
            vals.append(f"{y:04d}{m:02d}")
            m += 1
            if m > 12:
                m = 1
                y += 1
        return vals

