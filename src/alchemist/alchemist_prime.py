# ===================================================================
# Archivo: alchemist_prime.py (v3.0 - Orquestador de Lotes por Profundidad)
# Autor: Colaboración entre el Ingeniero Principal y el Arquitecto de Software
# ===================================================================
# Implementa un motor ETL declarativo que analiza las dependencias del
# pipeline y lo ejecuta en lotes optimizados por profundidad (DAG).
# Esta arquitectura respeta el orden secuencial de las transformaciones
# mientras maximiza la eficiencia de Polars.
# ===================================================================

import polars as pl
import pandas as pd
import json
import logging
import unicodedata
from typing import Dict, Callable, Any, Optional, List

# --- NUEVO: Importaciones para conectores ---
from sqlalchemy import create_engine

# --- Configuración del Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

class AlchemistPrime:
    """
    AlchemistPrime (v3.0) - Motor ETL con ejecución por lotes de profundidad (DAG).

    Esta versión resuelve el conflicto fundamental entre la eficiencia de Polars
    y la naturaleza secuencial de los pipelines con dependencias.

    Mejoras Clave:
    - El método `transmute` ahora analiza el grafo de dependencias y ejecuta
      el pipeline en "capas", garantizando que las columnas fuente existan
      antes de ser utilizadas.
    - Máxima eficiencia al agrupar el mayor número de pasos independientes en cada lote.
    - Detección de dependencias circulares o rotas.
    - Métodos `agregar_status_y_errores` y `limpiar_columnas_intermedias`
      optimizados y robustos.
    """

    def _normalize_config(self):
        """Normaliza la configuración para trazabilidad y robustez."""
        config_pd = self._config.to_pandas()
        if 'target_column' not in config_pd.columns:
            config_pd['target_column'] = config_pd.apply(
                lambda row: f"{row['source_column']}__{row['step_id']}", axis=1
            )
        # El campo 'is_new_column' ya no es necesario en la nueva arquitectura
        self._config = pl.from_pandas(config_pd)

    def __init__(
        self,
        data_df: pd.DataFrame,
        config_df: pd.DataFrame,
        dictionary_df: pd.DataFrame,
        logger: Optional[logging.Logger] = None
    ):
        """Inicializa la instancia de AlchemistPrime."""
        self.logger = logger or logging.getLogger("AlchemistPrime")
        self.logger.info("--- Inicializando AlchemistPrime v3.1 (con Conectores Dinámicos) ---")

        # --- CONVERSIÓN ÚNICA AL INICIO ---
        self._df = pl.from_pandas(data_df)
        self._dictionary = pl.from_pandas(dictionary_df)
        self._config = pl.from_pandas(config_df).sort("step_id")
        
        # --- NUEVO: Caché para tablas de enriquecimiento ---
        self._enrichment_cache: Dict[str, pl.DataFrame] = {}

        self._normalize_config()

        # Validación de configuración inicial
        self._validate_initial_config()

        # Pre-cálculo de mapas y registro de funciones para máxima eficiencia
        self._step_functions = self._get_step_functions()
        self._homologation_maps = self._build_homologation_maps(self._dictionary)

        self.logger.info("--- AlchemistPrime listo para orquestar. ---")

    def _validate_initial_config(self):
        """Valida que la configuración tenga los campos requeridos."""
        required_fields = {'step_id', 'step_type', 'source_column', 'target_column', 'step_params'}
        missing_fields = required_fields - set(self._config.columns)
        if missing_fields:
            raise ValueError(f"La configuración debe contener las columnas: {missing_fields}")

    def transmute(self) -> 'AlchemistPrime':
        """
        Orquesta y ejecuta el pipeline completo, respetando las dependencias
        entre pasos y ejecutando en lotes optimizados por profundidad (DAG).
        """
        self.logger.info("--- Analizando dependencias y construyendo lotes de ejecución ---")

        all_rules = self._config.to_dicts()
        processed_steps = set()
        batch_num = 0

        # --- MEJORA: Identificar los tipos de pasos que no dependen de una columna fuente ---
        generator_step_types = {"GENERATE_ROW_ID", "ASSIGN_CONSTANT"}

        while len(processed_steps) < len(all_rules):
            available_columns = set(self._df.columns)
            
            # Identificar reglas cuyas dependencias (source_column) ya están satisfechas
            rules_for_this_batch = [
                rule for rule in all_rules
                if rule['step_id'] not in processed_steps and (
                    # 1. Pasos que usan columnas existentes
                    rule.get('source_column') in available_columns or
                    # 2. Pasos que no especifican una columna fuente
                    not rule.get('source_column') or
                    # 3. Pasos generadores que no necesitan una columna fuente real
                    rule.get('step_type') in generator_step_types
                )
            ]

            if not rules_for_this_batch:
                unprocessed = [r for r in all_rules if r['step_id'] not in processed_steps]
                missing_deps = {r['source_column'] for r in unprocessed if r.get('source_column')} - available_columns
                error_msg = (f"Error de dependencia: No se pueden procesar más pasos. "
                             f"Posible dependencia circular o columnas fuente faltantes: {missing_deps}. "
                             f"Pasos sin procesar: {[r['step_id'] for r in unprocessed]}")
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            self.logger.info(f"--- Lote de Ejecución #{batch_num}: Procesando {len(rules_for_this_batch)} pasos ---")
            expressions_to_execute: List[pl.Expr] = []

            for rule in rules_for_this_batch:
                step_id, step_type, tgt = rule['step_id'], rule['step_type'], rule['target_column']
                status_col, msg_col = f"status_alchemist_{tgt}", f"msg_error_alchemist_{tgt}"

                builder_function = self._step_functions.get(step_type)
                if builder_function:
                    try:
                        expr = builder_function(rule)
                        # Si la función devuelve una expresión, se añade al lote
                        if expr is not None:
                            expressions_to_execute.extend([expr, pl.lit("OK").alias(status_col), pl.lit("").alias(msg_col)])
                            self.logger.info(f"step_id={step_id}: Paso '{step_type}' construido para el lote #{batch_num}.")
                        # Si no devuelve expresión, puede ser una acción directa (JOIN) o un skip
                        else:
                            # Para JOIN, el log ya se emitió en el constructor. Aquí solo ponemos el status.
                            if step_type == "ENRICH_WITH_JOIN":
                                expressions_to_execute.extend([pl.lit("OK").alias(status_col), pl.lit("").alias(msg_col)])
                            else:
                                expressions_to_execute.extend([pl.lit("SKIPPED").alias(status_col), pl.lit(f"Paso '{step_type}' no produjo expresión.").alias(msg_col)])
                    except Exception as ex:
                        error_msg = f"step_id={step_id}: Error en paso '{step_type}': {ex}"
                        expressions_to_execute.extend([pl.lit("ERROR").alias(status_col), pl.lit(error_msg).alias(msg_col)])
                        self.logger.error(error_msg)
                else:
                    expressions_to_execute.extend([pl.lit("UNKNOWN").alias(status_col), pl.lit(f"Tipo de paso '{step_type}' no reconocido.").alias(msg_col)])
                
                processed_steps.add(step_id)

            if expressions_to_execute:
                try:
                    self._df = self._df.with_columns(expressions_to_execute)
                except Exception as ex:
                    self.logger.error(f"Error Crítico al ejecutar el lote #{batch_num}: {ex}")
                    raise
            
            batch_num += 1

        self.logger.info("--- Todos los lotes del pipeline han sido ejecutados. ---")
        return self

    def _build_dependency_graph(self) -> List[List[int]]:
        """
        Construye el grafo de dependencias entre los pasos del pipeline.

        Devuelve una lista de capas, donde cada capa es una lista de step_id
        que pueden ser ejecutados en paralelo (sin dependencias entre ellos).
        """
        graph = {}
        in_degree = {}

        # Inicializar el grafo y los contadores de grado de entrada
        for rule in self._config.iter_rows(named=True):
            step_id = rule.get('step_id')
            src = rule.get('source_column')
            tgt = rule.get('target_column')

            graph[step_id] = {'rule': rule, 'dependencies': [], 'dependents': []}
            in_degree[step_id] = 0

        # Construir el grafo: para cada regla, añadirla como dependiente
        # de las reglas de las que depende (según la configuración)
        for rule in self._config.iter_rows(named=True):
            step_id = rule.get('step_id')
            src = rule.get('source_column')
            tgt = rule.get('target_column')

            if src and src in graph:
                # Añadir esta regla como dependiente de las reglas fuente
                graph[src]['dependents'].append(step_id)
                # Aumentar el contador de grado de entrada de este paso
                in_degree[step_id] += 1
            else:
                # Si no hay dependencia, esta regla puede ejecutarse primero
                graph[step_id]['dependencies'] = []

        # --- NUEVO: Detección de ciclos ---
        if self._has_cycles(graph):
            self.logger.error("El grafo de dependencias tiene ciclos. No se puede ejecutar el pipeline.")
            return []

        # --- NUEVO: Ordenar por capas ---
        return self._topological_sort(graph, in_degree)

    def _has_cycles(self, graph: Dict) -> bool:
        """
        Detecta ciclos en el grafo de dependencias usando búsqueda en profundidad.

        Devuelve True si se detecta un ciclo, False en caso contrario.
        """
        visited = set()
        rec_stack = set()

        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph[node]['dependents']:
                if dfs(neighbor):
                    return True
            rec_stack.remove(node)
            return False

        # Ejecutar DFS desde cada nodo
        for node in graph:
            if dfs(node):
                return True
        return False

    def _topological_sort(self, graph: Dict, in_degree: Dict) -> List[List[int]]:
        """
        Ordena el grafo de dependencias topológicamente y lo agrupa en capas.

        Devuelve una lista de capas, donde cada capa es una lista de step_id
        que pueden ser ejecutados en paralelo (sin dependencias entre ellos).
        """
        # --- NUEVO: Usar deque para eficiencia en pop de izquierda ---
        from collections import deque

        # Inicializar la cola con los nodos de grado de entrada 0
        zero_in_degree = deque([node for node, degree in in_degree.items() if degree == 0])
        sorted_layers = []

        while zero_in_degree:
            current_layer = []
            next_zero_in_degree = deque()

            while zero_in_degree:
                node = zero_in_degree.popleft()
                current_layer.append(node)

                # Reducir el grado de entrada de los dependientes
                for neighbor in graph[node]['dependents']:
                    in_degree[neighbor] -= 1
                    # Si el grado de entrada del vecino es 0, añadir a la cola
                    if in_degree[neighbor] == 0:
                        next_zero_in_degree.append(neighbor)

            sorted_layers.append(current_layer)
            zero_in_degree = next_zero_in_degree

        # --- NUEVO: Verificación de que todos los nodos fueron procesados ---
        if len(sorted_layers) * len(graph) == sum(in_degree.values()):
            self.logger.warning("No se procesaron todos los nodos. Posible dependencia circular o rota.")

        return sorted_layers

    def to_pandas(self) -> pd.DataFrame:
        """
        Punto de salida del pipeline.

        Convierte el DataFrame interno de Polars, ya completamente transformado,
        de vuelta a un DataFrame de Pandas.

        Returns:
            pd.DataFrame: El DataFrame final y procesado.
        """
        self.logger.info("--- Finalizando: Convirtiendo resultado de Polars a Pandas ---")
        return self._df.to_pandas()

    # --- "Fábrica" de constructores de expresiones ---
    def _get_step_functions(self) -> Dict[str, Callable]:
        """
        Mapea cada step_type a la función que construye su expresión de Polars.
        Este es el registro central de todas las capacidades de transformación.
        """
        return {
            "CLEAN_TEXTO_NLP": self._build_clean_text_expr,
            "CLEAN_IDENTIFIER": self._build_clean_identifier_expr,
            "CLEAN_ID_NUMERICO": self._build_clean_numeric_expr,
            "CLEAN_FECHA": self._build_clean_date_expr,
            "DATETIME_BUILDER": self._build_datetime_expr,
            "ASSIGN_CONSTANT": self._build_constant_expr,
            "HOMOLOGATE": self._build_homologate_expr,
            "GENERATE_ROW_ID": self._build_row_id_expr,
            "CONDITIONAL_MAPPING": self._build_conditional_expr,
            "ENRICH_WITH_JOIN": self._build_enrich_with_join_expr # <-- NUEVO PASO REGISTRADO
        }

    def _build_enrich_with_join_expr(self, rule: dict) -> None:
        """
        Enriquece el DataFrame principal con un JOIN.
        Carga dinámicamente la tabla derecha desde la fuente especificada.
        Esta operación modifica directamente self._df y no devuelve una expresión.
        """
        params = json.loads(rule['step_params'])
        
        # --- 1. Extraer y validar parámetros ---
        source_params = params.get('source')
        left_on = params.get('left_on')
        right_on = params.get('right_on')
        select_rename_map = params.get('select', {})
        how = params.get('how', 'left')

        if not all([source_params, left_on, right_on, select_rename_map]):
            raise ValueError(f"ENRICH_WITH_JOIN (step_id={rule['step_id']}): Faltan parámetros (source, left_on, right_on, select).")

        if how not in ['left', 'inner']:
            raise ValueError(f"ENRICH_WITH_JOIN (step_id={rule['step_id']}): Tipo de join '{how}' no soportado. Use 'left' o 'inner'.")

        # --- 2. Cargar tabla derecha usando el conector ---
        right_df = self._get_enrichment_table(source_params)

        # --- 3. Ejecutar el JOIN ---
        original_cols = self._df.columns
        
        joined_df = self._df.join(
            right_df,
            left_on=left_on,
            right_on=right_on,
            how=how
        )

        # --- 4. Seleccionar y renombrar columnas ---
        final_cols_selection = original_cols.copy()
        
        for col_from_right, new_name in select_rename_map.items():
            if col_from_right not in joined_df.columns:
                 self.logger.warning(f"ENRICH_WITH_JOIN (step_id={rule['step_id']}): La columna '{col_from_right}' no se encontró en la tabla unida.")
                 continue
            # Polars añade un sufijo "_right" si la columna ya existe. Lo manejamos.
            col_to_rename = col_from_right if col_from_right in joined_df.columns else f"{col_from_right}_right"
            joined_df = joined_df.rename({col_to_rename: new_name})
            final_cols_selection.append(new_name)
        
        self._df = joined_df.select(final_cols_selection)
        self.logger.info(f"ENRICH_WITH_JOIN (step_id={rule['step_id']}): Join con fuente '{source_params.get('source_type')}' completado.")
        
        # No devuelve expresión porque la operación ya se realizó
        return None

    # --- Constructores de Expresiones Individuales ---

# DENTRO de la clase AlchemistPrime

    def _build_conditional_expr(self, rule: dict) -> Optional[pl.Expr]:
        """
        Construye una expresión condicional (CASE WHEN) a partir de una lista de reglas.
        Soporta operadores como '==', '!=', '>', '>=', '<', '<=', 'contains'.
        """
        params = json.loads(rule['step_params'])
        source_col = rule.get('source_column')
        target_col = rule.get('target_column')
        
        if not source_col or source_col not in self._df.columns:
            self.logger.warning(f"CONDITIONAL_MAPPING: Columna fuente '{source_col}' no existe o no se especificó.")
            return None
            
        rules_list = params.get('rules', [])
        default_val = params.get('default')

        # Creamos el objeto de la columna sobre la que operaremos
        col_expr = pl.col(source_col)

        # Empezamos a construir la cadena de when/then
        when_then_chain = None
        
        for condition_rule in rules_list:
            if_clause = condition_rule.get('if', {})
            then_val = condition_rule.get('then')
            
            operator = if_clause.get('operator', '==')
            value = if_clause.get('value')

            # --- Despachador de Condiciones ---
            if operator == '==':
                condition = (col_expr == value)
            elif operator == '!=':
                condition = (col_expr != value)
            elif operator == '>':
                condition = (col_expr > value)
            elif operator == '>=':
                condition = (col_expr >= value)
            elif operator == '<':
                condition = (col_expr < value)
            elif operator == '<=':
                condition = (col_expr <= value)
            elif operator == 'contains':
                condition = col_expr.cast(pl.Utf8).str.contains(str(value))
            # --- NUEVA LÓGICA ---
            elif operator == 'is_null':
                condition = col_expr.is_null()
            elif operator == 'is_not_null':
                condition = col_expr.is_not_null()
            # --- FIN NUEVA LÓGICA ---
            else:
                self.logger.warning(f"CONDITIONAL_MAPPING: Operador '{operator}' no reconocido.")
                continue # Salta a la siguiente regla

            # Encadenamos la condición
            if when_then_chain is None:
                when_then_chain = pl.when(condition).then(pl.lit(then_val))
            else:
                when_then_chain = when_then_chain.when(condition).then(pl.lit(then_val))

        if when_then_chain is None:
            self.logger.warning("CONDITIONAL_MAPPING: No se definieron reglas válidas.")
            return None

        # --- MEJORA: Manejar default desde otra columna ---
        default_expr = pl.lit(default_val)
        if isinstance(default_val, str) and default_val in self._df.columns:
            self.logger.info(f"CONDITIONAL_MAPPING: Usando la columna '{default_val}' como valor por defecto.")
            default_expr = pl.col(default_val)

        # Añadimos la cláusula 'else' (default) al final de la cadena
        final_expr = when_then_chain.otherwise(default_expr)

        return final_expr.alias(target_col)

    def _build_row_id_expr(self, rule: dict) -> Optional[pl.Expr]:
        """
        Construye una expresión para generar un número de fila (consecutivo),
        potencialmente particionado por una o más columnas.
        """
        params = json.loads(rule['step_params'])
        target_col = rule['target_column']
        partition_cols = params.get('partition_by')

        # --- MEJORA: Validación robusta de partition_cols ---
        if partition_cols:
            # 1. Asegurarse de que sea una lista
            if not isinstance(partition_cols, list):
                self.logger.warning(
                    f"GENERATE_ROW_ID: 'partition_by' debe ser una lista de nombres de columnas, pero se recibió {type(partition_cols)}. "
                    "Se creará un consecutivo global en su lugar."
                )
                partition_cols = None # Forzar consecutivo global
            else:
                # 2. Verificar que todas las columnas de la lista existan
                non_existent_cols = [col for col in partition_cols if col not in self._df.columns]
                if non_existent_cols:
                    self.logger.error(
                        f"GENERATE_ROW_ID: Las siguientes columnas en 'partition_by' no existen: {non_existent_cols}. "
                        "No se puede generar el consecutivo particionado."
                    )
                    return None # Detener la creación de esta expresión

        if partition_cols:
            # Si se especifica 'partition_by' y es válido, crea un row_number() dentro de cada grupo.
            self.logger.info(f"GENERATE_ROW_ID: Creando consecutivo particionado por {partition_cols}.")
            # Usamos pl.len() en lugar del obsoleto pl.count()
            return (pl.arange(0, pl.len()).over(partition_cols) + 1).alias(target_col)
        else:
            # Si no, crea un row_number simple para todo el DataFrame.
            self.logger.info("GENERATE_ROW_ID: Creando consecutivo global.")
            # Usamos pl.len() en lugar del obsoleto pl.count()
            return (pl.int_range(1, pl.len() + 1)).alias(target_col)

    def _build_clean_text_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión de Polars para la limpieza profunda de texto."""
        source_col, target_col = rule['source_column'], rule['target_column']
        if source_col not in self._df.columns:
            self.logger.warning(f"CLEAN_TEXTO_NLP: Columna fuente '{source_col}' no existe.")
            return None

        expr = pl.col(source_col).cast(pl.Utf8).str.to_lowercase()
        expr = expr.map_elements(lambda s: unicodedata.normalize('NFD', s) if s else s, return_dtype=pl.Utf8)
        expr = expr.map_elements(lambda s: ''.join(c for c in s if unicodedata.category(c) != 'Mn') if s else s, return_dtype=pl.Utf8)
        expr = expr.str.replace_all(r'[^\w\s]', ' ').str.replace_all(r'\s+', ' ').str.strip_chars()
        expr = expr.map_elements(lambda x: None if x == "" else x)
        return expr.alias(target_col)

    def _build_clean_identifier_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión para crear un identificador estandarizado."""
        cleaned_text_expr = self._build_clean_text_expr(rule)
        if cleaned_text_expr is None:
            return None
        target_col = rule['target_column']
        identifier_expr = cleaned_text_expr.fill_null("").str.replace_all(r'\s', '_')
        return identifier_expr.alias(target_col)

    def _build_clean_numeric_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión para limpiar y estandarizar IDs numéricos."""
        source_col, target_col = rule['source_column'], rule['target_column']
        if source_col not in self._df.columns:
            self.logger.warning(f"CLEAN_ID_NUMERICO: Columna fuente '{source_col}' no existe.")
            return None
        expr = pl.col(source_col).cast(pl.Utf8).str.replace_all(r'[^0-9]', '')
        expr = expr.map_elements(lambda x: None if x == "" else x)
        return expr.alias(target_col)

    def _build_clean_date_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión para limpiar y parsear fechas de forma robusta."""
        source_col, target_col = rule['source_column'], rule['target_column']
        if source_col not in self._df.columns:
            self.logger.warning(f"CLEAN_FECHA: Columna fuente '{source_col}' no existe.")
            return None

        def parse_date(x: Any) -> Optional[str]:
            if x is None or str(x).lower() in ['<na>', 'nan', 'none', 'na', '']:
                return None
            try:
                val = float(x)
                if 10000 < val < 100000:
                    return (pd.Timestamp('1899-12-30') + pd.Timedelta(days=val)).strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass
            try:
                dt = pd.to_datetime(x, errors='coerce', dayfirst=True)
                return dt.strftime('%Y-%m-%d') if pd.notna(dt) else None
            except Exception:
                return None

        return pl.col(source_col).map_elements(parse_date, return_dtype=pl.Utf8).alias(target_col)

    def _build_datetime_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión para combinar columnas de fecha y hora."""
        params = json.loads(rule['step_params'])
        source_col, target_col = rule['source_column'], rule['target_column']
        time_col = params.get('time_col')
        fmt = params.get('format', "%Y-%m-%d %H:%M")
        if source_col not in self._df.columns or time_col not in self._df.columns:
            self.logger.warning(f"DATETIME_BUILDER: Columnas '{source_col}' o '{time_col}' no existen.")
            return None
        expr = (pl.col(source_col).cast(pl.Utf8) + " " + pl.col(time_col).cast(pl.Utf8)) \
               .str.to_datetime(fmt, strict=False, exact=False) \
               .alias(target_col)
        return expr

    def _build_constant_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión para asignar un valor constante a una columna."""
        params = json.loads(rule['step_params'])
        target_col = rule['target_column']
        value = params.get('value')
        if value is None:
            self.logger.warning(f"ASSIGN_CONSTANT: No se especificó el valor constante para '{target_col}'.")
            return None
        return pl.lit(value).alias(target_col)

    def _build_homologate_expr(self, rule: dict) -> Optional[pl.Expr]:
        """Construye una expresión para homologar valores usando un diccionario."""
        params = json.loads(rule['step_params'])
        source_col, target_col = rule['source_column'], rule['target_column']
        dictionary_key = params.get('dictionary_key')
        if source_col not in self._df.columns:
            self.logger.warning(f"HOMOLOGATE: Columna fuente '{source_col}' no existe.")
            return None
        h_map = self._homologation_maps.get(dictionary_key)
        if h_map:
            return pl.col(source_col).replace_strict(h_map, default=pl.col(source_col)).alias(target_col)
        else:
            self.logger.warning(f"HOMOLOGATE: Clave de diccionario '{dictionary_key}' no encontrada.")
            return None

    def _build_homologation_maps(self, dictionary_pl: pl.DataFrame) -> Dict[str, Dict]:
        """Pre-calcula y almacena los diccionarios de homologación desde la tabla de diccionario."""
        maps = {}
        unique_concepts = dictionary_pl.get_column('concepto_normal').drop_nulls().unique().to_list()
        for concept in unique_concepts:
            group = dictionary_pl.filter(pl.col('concepto_normal') == concept)
            maps[concept] = dict(zip(group['valor_normal'].to_list(), group['es_sinonimo_de'].to_list()))
        self.logger.info(f"Se han pre-calculado {len(maps)} mapas de homologación.")
        return maps

    # --- Subsistema de Conectores Dinámicos ---

    def _get_enrichment_table(self, source_params: dict) -> pl.DataFrame:
        """
        Despachador principal para cargar tablas de enriquecimiento.
        Utiliza un caché para evitar lecturas redundantes.
        """
        source_type = source_params.get('source_type')
        cache_key = json.dumps(source_params, sort_keys=True)

        if cache_key in self._enrichment_cache:
            self.logger.info(f"Cargando tabla desde caché para fuente: {source_type}")
            return self._enrichment_cache[cache_key]

        self.logger.info(f"Cargando tabla desde nueva fuente: {source_type}")
        
        if source_type == 'postgresql':
            df = self._load_from_postgres(source_params)
        elif source_type == 'excel':
            df = self._load_from_excel(source_params)
        elif source_type == 'csv':
            df = self._load_from_csv(source_params)
        else:
            raise ValueError(f"Tipo de fuente '{source_type}' no soportado.")
        
        self._enrichment_cache[cache_key] = df
        return df

    def _load_from_postgres(self, params: dict) -> pl.DataFrame:
        """Carga datos desde una base de datos PostgreSQL."""
        # Aquí deberías tener un sistema seguro para manejar credenciales (ej. variables de entorno)
        # Por simplicidad, se asume una URL de conexión.
        db_url = params.get('db_url') # "postgresql://user:password@host:port/database"
        schema = params.get('schema')
        table = params.get('table')
        query = f'SELECT * FROM "{schema}"."{table}"'
        
        if 'query' in params: # Permite una query completa si se especifica
            query = params['query']
        
        if not db_url or not query:
            raise ValueError("Para PostgreSQL se requiere 'db_url' y 'query' o 'schema'/'table'.")

        engine = create_engine(db_url)
        with engine.connect() as connection:
            df_pd = pd.read_sql(query, connection)
            return pl.from_pandas(df_pd)

    def _load_from_excel(self, params: dict) -> pl.DataFrame:
        """Carga datos desde un archivo Excel."""
        path = params.get('path')
        sheet_name = params.get('sheet_name', 0) # Por defecto la primera hoja
        
        if not path:
            raise ValueError("Para Excel se requiere 'path'.")
            
        df_pd = pd.read_excel(path, sheet_name=sheet_name)
        return pl.from_pandas(df_pd)

    def _load_from_csv(self, params: dict) -> pl.DataFrame:
        """Carga datos desde un archivo CSV."""
        path = params.get('path')
        separator = params.get('separator', ',')
        
        if not path:
            raise ValueError("Para CSV se requiere 'path'.")
            
        return pl.read_csv(path, separator=separator)

    def limpiar_columnas_intermedias(self) -> 'AlchemistPrime':
        """
        Elimina todas las columnas de status y error generadas por paso,
        dejando solo las columnas de datos y los campos globales de auditoría
        (`status_alchemist` y `error_msg`).
        """
        cols_to_drop = [c for c in self._df.columns if c.startswith("status_alchemist_") or c.startswith("msg_error_alchemist_")]
        self._df = self._df.drop(cols_to_drop)
        self.logger.info(f"Se eliminaron {len(cols_to_drop)} columnas intermedias de auditoría.")
        return self

    def agregar_status_y_errores(self) -> 'AlchemistPrime':
        """
        Agrega dos columnas globales al DataFrame para auditoría y análisis por fila:

        - status_alchemist: Estado global de la fila ("OK" si todas las transformaciones fueron exitosas,
          "ERROR" si alguna falló).
        - error_msg: Array de dicts con los errores detectados en cada fila. Cada dict contiene:
            * "column_name": nombre único de la columna destino y el step_id (ej: "tipo_afiliado__20").
            * "error": mensaje descriptivo del error en ese paso.

        Uso:
        - Llamar después de ejecutar el pipeline (transmute) y antes de limpiar columnas intermedias o convertir a pandas.
        - Permite filtrar filas problemáticas y explotar los errores para análisis avanzado o desarrollo de agentes IA.

        Ejemplo:
        >>> alchemist.transmute()
        >>> alchemist.agregar_status_y_errores()
        >>> alchemist.limpiar_columnas_intermedias()
        >>> df_final = alchemist.to_pandas()

        Ventajas:
        ---------
        - Permite auditoría avanzada y profiling por fila y por paso.
        - Facilita el desarrollo de agentes IA para análisis de calidad y recomendaciones automáticas.
        - Optimiza la entrega de resultados, manteniendo solo la información relevante para el usuario final.

        Returns:
        -------
        AlchemistPrime
            La propia instancia, permitiendo el encadenamiento de métodos.
        """
        status_cols = [col for col in self._df.columns if col.startswith("status_alchemist_")]
        msg_cols = [col for col in self._df.columns if col.startswith("msg_error_alchemist_")]
        
        if not status_cols:
            self.logger.warning("No se encontraron columnas de status para agregar. Omitiendo paso.")
            return self

        # --- MEJORA: Separar la creación de columnas dependientes ---
        
        # 1. Crear la columna 'status_alchemist'
        df_with_status = self._df.with_columns(
            pl.when(pl.concat_list(status_cols).list.contains("ERROR"))
              .then(pl.lit("ERROR"))
              .otherwise(pl.lit("OK"))
              .alias("status_alchemist")
        )

        # 2. Usar la nueva columna 'status_alchemist' para crear 'error_msg'
        col_step_map = {f"msg_error_alchemist_{r['target_column']}": f"{r['target_column']}__{r['step_id']}" 
                        for r in self._config.to_dicts()}

        self._df = df_with_status.with_columns(
            pl.when(pl.col("status_alchemist") == "ERROR")
              .then(
                  pl.concat_list([
                      pl.struct([
                          pl.lit(col_step_map.get(msg_col, msg_col)).alias("column_name"),
                          pl.col(msg_col).alias("error")
                      ]) for msg_col in msg_cols if msg_col in col_step_map
                  ]).list.filter(pl.element().struct.field("error") != "")
              )
              .otherwise(pl.lit(None, dtype=pl.List(pl.Struct([pl.Field("column_name", pl.Utf8), pl.Field("error", pl.Utf8)]))))
              .alias("error_msg")
        )
        return self

# ===================================================================
# FIN DE AlchemistPrime v3.0: Orquestador de Lotes por Profundidad
# ===================================================================