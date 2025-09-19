from typing import Any, Dict, List, Optional, Set, Tuple
import re
import json


def compile_alchemist_flow(process_table: List[Dict[str, Any]], filter_process_key: Optional[str] = None):
    """
    Compila un DataFrame de configuración (df_flow) a partir de una tabla unificada de procesos.
    Filtra por process_key si se proporciona.

    Devuelve un dict con la clave 'df_flow' para compatibilidad con Shekina.
    """
    try:
        import pandas as pd  # local import
        rows = []
        for row in process_table or []:
            if row.get('opcode') != 'alchemist.step':
                continue
            if filter_process_key and row.get('process_key') != filter_process_key:
                continue
            pload = row.get('payload', {}) or {}
            step_type = pload.get('step_type')
            source_column = pload.get('source_column')
            target_column = pload.get('target_column')
            step_params = pload.get('step_params', {})
            step_id = pload.get('step_id')
            if step_id is None:
                m = re.findall(r"\d+", str(row.get('id', '')))
                step_id = int(m[0]) if m else len(rows) + 1
            if isinstance(step_params, (dict, list)):
                step_params = json.dumps(step_params, ensure_ascii=False)
            rows.append({
                'row_id': len(rows) + 1,
                'step_id': step_id,
                'source_table': pload.get('source_table'),
                'source_column': source_column,
                'step_type': step_type,
                'step_params': step_params,
                'target_column': target_column,
            })
        if not rows:
            return {'error': 'No se encontraron filas alchemist.step para compilar.'}
        df_flow = pd.DataFrame(rows).sort_values('step_id').reset_index(drop=True)
        return {'df_flow': df_flow}
    except Exception as ex:
        return {'error': f'Error compilando df_flow: {ex}'}


def build_dependency_waves(
    deps_map: Dict[str, Set[str]],
    *,
    universe: Optional[Set[str]] = None,
    allow_external_deps: bool = True,
    strict_dependencies: bool = False,
) -> Dict[str, Any]:
    """
    Construye olas (niveles) de ejecución respetando dependencias (Kahn-like).

    - deps_map: mapa item -> conjunto de dependencias (strings)
    - universe: conjunto de items válidos (si None se toma del propio deps_map)
    - allow_external_deps: si False, error si una dependencia no está en el universo
    - strict_dependencies: si True, error si quedan ciclos

    Retorna dict con:
    - levels: List[List[str]] olas
    - remaining: List[str] items con ciclos (si los hay)
    - externals: Dict[str, List[str]] dependencias externas por item (si las hay)
    """
    items = list(deps_map.keys())
    universe = set(items) if universe is None else set(universe)
    externals: Dict[str, List[str]] = {}

    if not allow_external_deps:
        for k, v in deps_map.items():
            ext = [d for d in v if d not in universe]
            if ext:
                externals[k] = ext
        if externals:
            return {
                'error': 'Dependencias externas no permitidas',
                'externals': externals
            }
    # intersectar deps con el universo
    deps = {k: set([d for d in v if d in universe]) for k, v in deps_map.items()}
    # Kahn por niveles
    levels: List[List[str]] = []
    remaining = {k: set(v) for k, v in deps.items()}
    while True:
        ready = [k for k, v in remaining.items() if len(v) == 0]
        if not ready:
            break
        levels.append(ready)
        for r in ready:
            remaining.pop(r, None)
        for k in list(remaining.keys()):
            remaining[k] -= set(ready)
    if remaining:
        if strict_dependencies:
            return {'error': 'Ciclo de dependencias detectado', 'remaining': list(remaining.keys())}
        levels.append(list(remaining.keys()))
    return {
        'levels': levels,
        'remaining': [] if not remaining else list(remaining.keys()),
        'externals': externals or {}
    }
