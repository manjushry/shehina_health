class Mirror:
    """
    Gestión de transacciones y manipulación de datos entre fuentes y destinos.
    Version: 1.0.0
    """
    __version__ = "1.0.0"
    def __init__(self, config):
        self.config = config
        # Implementación futura
# alef/k01_python/mirror/db_api.py (Versión 3.2.0 - Lista para Producción)

import pandas as pd
from sqlalchemy import create_engine, text, inspect, Table, MetaData
from sqlalchemy.engine import Engine
from sqlalchemy.dialects import postgresql
from typing import Dict, Any, List
import logging
import sys
import re


# --- CLASE PRINCIPAL ---
class Mirror:
    """
    Gestiona una conexión a una base de datos, proporcionando métodos de alto nivel
    para operaciones de lectura y escritura. (Versión Omega - Fusionada)
    """
       
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa la API de base de datos a partir de un diccionario de configuración.
        """
        # 1. Configurar y crear el logger COMO UN ATRIBUTO DE LA INSTANCIA
        self.logger = logging.getLogger(f"Mirror.{config.get('database')}")
        self.logger.setLevel(logging.INFO)
        # Opcional: Asegurarse de que los logs aparezcan en la consola de KNIME
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout) # Usar sys.stdout para la consola de KNIME
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info(f"Mirror: Iniciando conexión con '{config.get('database')}' en '{config.get('host')}'...")
        if not all(k in config for k in ['db_type', 'user', 'password', 'host', 'port', 'database']):
            raise ValueError("El diccionario de configuración no contiene todas las claves requeridas.")
            
        self.config = config
        self.engine: Engine = self._create_engine()
        
        # --- LÓGICA DE SCHEMA CONSCIENTE DEL DIALECTO ---
        # Si el dialecto es postgresql, el schema es válido. Para otros, es None.
        if self.config['db_type'] == 'postgresql':
            self.default_schema = self.config.get('schema')
        else:
            self.default_schema = None
        
        self.logger.info(f"  -> Schema por defecto establecido en: '{self.default_schema or 'No aplica'}'.")

    def _create_engine(self) -> Engine:
        """
        Método privado para crear el motor de SQLAlchemy basado en la configuración.
        Ahora incluye manejo explícito de codificación y escapado de contraseñas.
        """
        db_type = self.config['db_type']
        self.logger.info(f"  -> Construyendo motor para el dialecto: '{db_type}'...")
        
        try:
            # --- REFACTORIZACIÓN APLICADA ---
            # Se escapa la contraseña una sola vez, antes de construir la URL.
            # Esto aplica de forma segura a todos los dialectos de BD.
            from urllib.parse import quote_plus
            password_escaped = quote_plus(self.config['password'])
            
            # --- BLOQUE DE CONSTRUCCIÓN DE URL Y ENGINE ---
            if db_type == 'postgresql':
                connection_url = (
                    f"postgresql+psycopg2://{self.config['user']}:{password_escaped}"
                    f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
                )
                engine = create_engine(connection_url, connect_args={'client_encoding': 'utf8'})
            
            elif db_type == 'mysql':
                connection_url = (
                    f"mysql+mysqlconnector://{self.config['user']}:{password_escaped}"
                    f"@{self.config['host']}:{self.config['port']}/{self.config['database']}?charset=utf8mb4"
                )
                engine = create_engine(connection_url)
                
            elif db_type == 'mssql':
                driver = self.config.get('driver')
                if not driver:
                    raise ValueError("Para 'mssql', se debe especificar el 'driver' en la configuración.")
                
                self.logger.info(f"     Usando driver ODBC para MSSQL: '{driver}'")
                driver_encoded = quote_plus(driver)
                
                connection_url = (
                    f"mssql+pyodbc://{self.config['user']}:{password_escaped}"
                    f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
                    f"?driver={driver_encoded}&charset=utf8"
                )
                engine = create_engine(connection_url)
                
            else:
                raise ValueError(f"Tipo de base de datos no soportado: {db_type}")

            # --- BLOQUE DE PRUEBA DE CONEXIÓN ---
            self.logger.info("  -> Probando la conexión con el nuevo motor...")
            with engine.connect() as connection:
                self.logger.info("  -> [OK] Conexión a la base de datos exitosa.")
            return engine
            
        except Exception as e:
            # ... (manejo de errores sin cambios) ...
            self.logger.error(f"ERROR CRÍTICO al crear el motor de conexión: {e}")
            if 'UnicodeDecodeError' in str(e) or 'charmap' in str(e):
                self.logger.error("     [DIAGNÓSTICO] DETECTADO ERROR DE UNICODE.")
                self.logger.error("     Causa probable: Caracteres especiales en la contraseña o parámetros de conexión.")
            raise

    def close(self):
        """Cierra el pool de conexiones del engine de forma segura."""
        if self.engine:
            self.engine.dispose()
            self.logger.info(f"  -> Mirror: Conexión a '{self.config['database']}' cerrada.")

    def read_sql(self, sql_query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Ejecuta una consulta SELECT y devuelve el resultado como un DataFrame de Pandas.
        Renombrado para mayor simplicidad. Usa sqlalchemy.text() para seguridad.
        """
        self.logger.info(f"  -> Mirror: Leyendo datos con la consulta: {sql_query[:150]}...")
        try:
            # Usar read_sql_query con text() es la práctica moderna y segura.
            return pd.read_sql_query(sql=text(sql_query), con=self.engine, params=params)
        except Exception as e:
            self.logger.error(f" ERROR al ejecutar la consulta de lectura: {e}")
            raise

# REEMPLAZA el método _get_table_column_order completo con este código:

    def _get_table_column_order(self, table_name: str, schema: str = None) -> List[str]:
        """
        (Método privado - REFACTORIZADO) Inspecciona la BD y devuelve la lista
        ordenada de nombres de columna. Ahora es compatible con todos los dialectos.
        """
        target_schema = schema or self.default_schema
        
        # Usamos el método _get_fully_qualified_table_name (que añadirás después)
        # solo para crear un mensaje de log claro y consistente.
        # Si aún no lo has añadido, puedes comentar esta línea temporalmente o usar una f-string simple.
        log_table_name = self._get_fully_qualified_table_name(table_name, target_schema)
        self.logger.info(f"  -> Obteniendo esquema para la tabla {log_table_name}...")
        
        try:
            inspector = inspect(self.engine)
            
            # El inspector de SQLAlchemy es lo suficientemente inteligente como para usar
            # el parámetro 'schema' correctamente para PostgreSQL, MSSQL y MySQL.
            columns = inspector.get_columns(table_name, schema=target_schema)
            
            if not columns:
                raise ValueError(f"La tabla {log_table_name} no existe o no tiene columnas.")
            
            column_order = [col['name'] for col in columns]
            self.logger.info(f"  -> Esquema obtenido con {len(column_order)} columnas: {column_order}")
            return column_order
        except Exception as e:
            self.logger.error(f" ERROR al obtener el esquema de la tabla: {e}")
            raise

    def prepare_dataframe(self, df: pd.DataFrame, table_name: str, schema: str = None) -> pd.DataFrame:
        """
        Valida, ordena y ajusta un DataFrame para que coincida con el esquema de una
        tabla de destino, manejando columnas faltantes y extra.
        """
        target_schema = schema or self.default_schema
        self.logger.info(f"  -> Preparando DataFrame para cargar en '{target_schema}.{table_name}'...")
        
        # 1. Obtener el esquema de la tabla de destino ("el contrato")
        db_column_order = self._get_table_column_order(table_name, target_schema)
        
        df_prepared = df.copy()

        # 2. Identificar columnas extra en el DataFrame (y eliminarlas)
        extra_in_df = set(df_prepared.columns) - set(db_column_order)
        if extra_in_df:
            df_prepared.drop(columns=list(extra_in_df), inplace=True)
            self.logger.info(f"     -> Columnas extra eliminadas del DataFrame: {list(extra_in_df)}")

        # 3. Identificar columnas que están en la BD pero faltan en el DataFrame
        missing_in_df = set(db_column_order) - set(df_prepared.columns)
        
        # --- LÓGICA DE CORRECCIÓN ---
        # 4. Construir la lista final de columnas para el reordenamiento.
        #    Esta lista contendrá solo las columnas que REALMENTE existen en nuestro
        #    DataFrame preparado, pero en el orden que dicta la base de datos.
        final_column_order = [col for col in db_column_order if col in df_prepared.columns]
        
        # 5. Forzar el orden final usando la lista corregida.
        df_prepared = df_prepared[final_column_order]
        self.logger.info("  -> [OK] Columnas alineadas con el orden de la base de datos.")

        # Opcional: Validar si alguna de las columnas faltantes es crítica
        if missing_in_df:
            # ... (la lógica que ya tenías para verificar si las faltantes tienen DEFAULT)...
            # Esto es bueno para logging y advertencias, pero no afecta el reordenamiento.
            self.logger.info(f"     -> Columnas faltantes en el DataFrame serán manejadas por la BD: {list(missing_in_df)}")

        # 6. Estandarizar valores nulos.
        df_prepared = df_prepared.where(pd.notna(df_prepared), None)
        self.logger.info("  -> [OK] Valores nulos estandarizados a 'None'.")
        
        return df_prepared

    def execute_sql(self, sql_statement: str):
        """
        Ejecuta una sentencia SQL que no devuelve resultados (DDL, TRUNCATE, etc.).
        Asegura el uso de transacciones para operaciones seguras.
        """
        self.logger.info(f"  -> Mirror: Ejecutando sentencia: {sql_statement[:150]}...")
        try:
            # `with self.engine.connect() as connection:` abre una conexión del pool.
            # `with connection.begin() as transaction:` inicia una transacción.
            # Si el bloque termina sin errores, la transacción hace COMMIT automáticamente.
            # Si ocurre un error, la transacción hace ROLLBACK automáticamente.
            with self.engine.connect() as connection:
                connection.execute(text(sql_statement))
            self.logger.info("  -> Sentencia ejecutada exitosamente.")
        except Exception as e:
            self.logger.error(f" ERROR al ejecutar la sentencia SQL: {e}")
            raise


# UPDATE DE COLUMNAS VALIDAS
    def update_from_dataframe(self, df: pd.DataFrame, table_name: str, join_on_column: str, schema: str = None) -> pd.DataFrame:
        """
        (PÚBLICO - v3.2.2 - MULTI-DIALECTO, TIPADO EXPLÍCITO Y LIMPIEZA GARANTIZADA)
        Actualiza filas existentes en una tabla de destino a partir de un DataFrame.

        Construye la sentencia UPDATE apropiada y ahora garantiza la correspondencia
        de tipos de datos y la eliminación de la tabla temporal.
        """
        target_schema = schema or self.default_schema
        full_table_name = self._get_fully_qualified_table_name(table_name, target_schema)

        if df.empty:
            self.logger.info("  -> DataFrame de entrada vacío. Se omite la operación UPDATE.")
            return pd.DataFrame([{"status": "SKIPPED", "message": "DataFrame vacío."}])

        if join_on_column not in df.columns:
            raise ValueError(f"La columna de cruce '{join_on_column}' no se encuentra en el DataFrame.")
        
        update_columns = [col for col in df.columns if col != join_on_column]
        if not update_columns:
            raise ValueError("El DataFrame no contiene columnas para actualizar (además de la columna de cruce).")

        import time, random, re
        sane_table_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
        temp_table_name_raw = f"temp_update_{sane_table_name}_{int(time.time())}_{random.randint(1000, 9999)}"
        full_temp_table_name = self._get_fully_qualified_table_name(temp_table_name_raw, target_schema)
        
        self.logger.info(f"MIRROR: Iniciando UPDATE masivo en '{full_table_name}' usando la tabla temporal '{temp_table_name_raw}'...")
        self.logger.info(f"   -> Cruce por columna: '{join_on_column}'")
        self.logger.info(f"   -> Columnas a actualizar: {update_columns}")

        # Mover la conexión fuera del try para que sea accesible en finally
        connection = self.engine.connect()
        try:
            self.logger.info("     -> Inspeccionando tipos de datos de la tabla de destino...")
            inspector = inspect(self.engine)
            columns_meta = inspector.get_columns(table_name, schema=target_schema)
            
            df_cols_set = set(df.columns)
            dtype_mapping = {
                col['name']: col['type'] for col in columns_meta if col['name'] in df_cols_set
            }
            self.logger.info(f"     -> [OK] Mapeo de tipos creado para {len(dtype_mapping)} columnas.")
            
            with connection.begin(): # Transacción para la operación
                self.logger.info(f"     -> Cargando {len(df)} filas en la tabla temporal...")
                df.to_sql(
                    temp_table_name_raw, 
                    connection, 
                    schema=target_schema, 
                    if_exists='replace', 
                    index=False, 
                    dtype=dtype_mapping
                )
                self.logger.info("     -> [OK] Carga a tabla temporal completada con tipos de datos correctos.")

                db_type = self.config['db_type']
                sql_update = ""

                if db_type == 'postgresql':
                    set_clause = ", ".join([f'"{col}" = temp."{col}"' for col in update_columns])
                    sql_update = f"""
                        UPDATE {full_table_name} AS target
                        SET {set_clause}
                        FROM {full_temp_table_name} AS temp
                        WHERE target."{join_on_column}" = temp."{join_on_column}";
                    """
                
                elif db_type == 'mssql':
                    set_clause = ", ".join([f'target.[{col}] = temp.[{col}]' for col in update_columns])
                    sql_update = f"""
                        UPDATE target
                        SET {set_clause}
                        FROM {full_table_name} AS target
                        INNER JOIN {full_temp_table_name} AS temp
                        ON target.[{join_on_column}] = temp.[{join_on_column}];
                    """
                
                elif db_type == 'mysql':
                    set_clause = ", ".join([f'target.`{col}` = temp.`{col}`' for col in update_columns])
                    sql_update = f"""
                        UPDATE {full_table_name} AS target
                        INNER JOIN {full_temp_table_name} AS temp
                        ON target.`{join_on_column}` = temp.`{join_on_column}`
                        SET {set_clause};
                    """
                
                else:
                    raise NotImplementedError(f"UPDATE FROM DATAFRAME no implementado para el dialecto '{db_type}'.")
                
                self.logger.info("     -> Ejecutando la sentencia UPDATE masiva...")
                result = connection.execute(text(sql_update))
                self.logger.info(f"     -> [OK] Operación completada. {result.rowcount} filas afectadas.")
            
            return pd.DataFrame([{"status": "SUCCESS", "filas_afectadas": result.rowcount}])

        except Exception as e:
            self.logger.error(f"  -> ERROR CRÍTICO durante el proceso de UPDATE masivo: {e}")
            raise e
        
        finally:
            self.logger.info(f"     -> Realizando limpieza: eliminando la tabla temporal '{temp_table_name_raw}'...")
            with connection.begin(): # El DROP necesita su propia (micro)transacción
                connection.execute(text(f'DROP TABLE IF EXISTS {full_temp_table_name};'))
            connection.close()
            self.logger.info("     -> [OK] Limpieza completada.")

# AÑADE este nuevo método completo en tu clase Mirror.
# Un buen lugar es después de 'prepare_dataframe' y antes de 'update_from_dataframe'.

    def _get_fully_qualified_table_name(self, table_name: str, schema: str = None) -> str:
        """
        (Privado) Construye el nombre de tabla completamente calificado y citado
        correctamente según el dialecto de la base de datos.
        """
        db_type = self.config['db_type']
        
        # La variable 'namespace' representa el contenedor de la tabla.
        # En PostgreSQL/MSSQL, es un 'schema'. En MySQL, es otra 'database'.
        namespace = schema or self.default_schema

        # --- Lógica Específica por Dialecto ---

        if db_type == 'mysql':
            # En MySQL, el 'namespace' es en realidad el nombre de la base de datos.
            # Si se proporciona, se usa el formato `database`.`table`.
            if namespace:
                return f'`{namespace}`.`{table_name}`'
            else:
                # Si no hay namespace, se asume la tabla está en la base de datos
                # actual de la conexión. Solo se cita el nombre de la tabla.
                return f'`{table_name}`'

        elif db_type == 'mssql':
            # MSSQL usa schemas y los cita con corchetes.
            if namespace:
                return f'[{namespace}].[{table_name}]'
            else:
                return f'[{table_name}]'
        
        else: # 'postgresql' es el default y el caso más común.
            # PostgreSQL usa schemas y los cita con comillas dobles.
            if namespace:
                return f'"{namespace}"."{table_name}"'
            else:
                return f'"{table_name}"'

# EL METODO MARAVILLA... 

   # --- MÉTODO DE ESCRITURA PRINCIPAL ---

    def upsert_dataframe(self, df: pd.DataFrame, table_name: str, conflict_columns: List[str], schema: str = None, action_on_conflict: str = 'UPDATE') -> pd.DataFrame:
        """
        (PÚBLICO - MÉTODO ÚNICO) Realiza una operación de UPSERT de alto rendimiento.

        Utiliza el patrón de tabla temporal + MERGE, que es eficiente tanto para
        inserciones, actualizaciones o una mezcla de ambas. La lógica interna
        construye la sentencia SQL apropiada ('DO UPDATE' o 'DO NOTHING')
        basándose en el parámetro `action_on_conflict`.
        """
        target_schema = schema or self.default_schema
        full_table_name = f'"{target_schema}"."{table_name}"'
        
        if df.empty:
            self.logger.info("  -> DataFrame de entrada vacío. Se omite la operación UPSERT.")
            return pd.DataFrame([{"status": "SKIPPED", "message": "DataFrame vacío."}])

        df_prepared = self.prepare_dataframe(df, table_name, target_schema)
        
        if df_prepared.empty:
            self.logger.warning("  -> DataFrame vacío después de la preparación. Se omite la operación UPSERT.")
            return pd.DataFrame([{"status": "SKIPPED", "message": "DataFrame vacío post-preparación."}])

        import time, random
        # Saneamiento del nombre de la tabla para seguridad
        sane_table_name = re.sub(r'[^a-zA-Z0-9_]', '', table_name)
        temp_table_name = f"temp_upsert_{sane_table_name}_{int(time.time())}_{random.randint(1000, 9999)}"
        
        self.logger.info(f"MIRROR: Iniciando UPSERT masivo en '{full_table_name}' usando la tabla temporal '{temp_table_name}'...")
        self.logger.info(f"   -> Acción en conflicto: {action_on_conflict.upper()}")

        try:
            # BUGFIX #1: Obtener los tipos de datos de la tabla de destino para garantizar
            # que la tabla temporal se cree con un esquema idéntico.
            inspector = inspect(self.engine)
            columns_meta = inspector.get_columns(table_name, schema=target_schema)
            dtype_mapping = {col['name']: col['type'] for col in columns_meta}

            with self.engine.connect() as connection:
                with connection.begin(): # Transacción atómica
                    self.logger.info(f"     -> Cargando {len(df_prepared)} filas en la tabla temporal...")
                    df_prepared.to_sql(temp_table_name, connection, schema=target_schema, if_exists='replace', index=False, dtype=dtype_mapping)
                    self.logger.info("     -> [OK] Carga a tabla temporal completada.")

                    db_type = self.config['db_type']
                    all_columns = df_prepared.columns.tolist()
                    
                    if db_type == 'postgresql':
                        sql_upsert = self._build_postgresql_merge_sql(full_table_name, f'"{target_schema}"."{temp_table_name}"', conflict_columns, all_columns, action_on_conflict)
                    # ... (otras implementaciones de dialecto) ...
                    else:
                        raise NotImplementedError(f"UPSERT no implementado para el dialecto '{db_type}'.")
                    
                    self.logger.info("     -> Ejecutando la sentencia UPSERT masiva...")
                    result = connection.execute(text(sql_upsert))
                    self.logger.info(f"     -> [OK] Operación completada. {result.rowcount} filas afectadas.")
            
            return pd.DataFrame([{"status": "SUCCESS", "filas_afectadas": result.rowcount}])

        except Exception as e:
            self.logger.error(f"  -> ERROR CRÍTICO durante el proceso de UPSERT masivo: {e}")
            raise e

    # --- MÉTODOS PRIVADOS DE IMPLEMENTACIÓN ---

    def _build_postgresql_merge_sql(self, target_table: str, temp_table: str, conflict_columns: List[str], all_columns: List[str], action: str) -> str:
        """
        (Privado) Construye la sentencia UPSERT de alto rendimiento para PostgreSQL.
        """
        self.logger.info(f"  -> Construyendo sentencia UPSERT para PostgreSQL (Acción: {action.upper()})...")
        
        cols_quoted = [f'"{col}"' for col in all_columns]
        conflict_cols_str = ", ".join([f'"{col}"' for col in conflict_columns])
        action_clause = "DO NOTHING"

        if action.upper() == 'UPDATE':
            update_cols = [f'"{col}" = EXCLUDED."{col}"' for col in all_columns if col not in conflict_columns]
            if update_cols:
                action_clause = f"DO UPDATE SET {', '.join(update_cols)}"
        
        sql = f"""
            INSERT INTO {target_table} ({', '.join(cols_quoted)})
            SELECT {', '.join(cols_quoted)} FROM {temp_table}
            ON CONFLICT ({conflict_cols_str}) {action_clause};
        """
        return sql

    def _build_mysql_merge_sql(self, target_table: str, temp_table: str, conflict_columns: List[str], all_columns: List[str], action: str) -> str:
        """
        (Privado) Construye la sentencia UPSERT de alto rendimiento para MySQL.
        
        Utiliza el dialecto 'INSERT ... ON DUPLICATE KEY UPDATE' para las actualizaciones
        y 'INSERT IGNORE' para las inserciones sin acción en conflicto.
        
        Nota: A diferencia de PostgreSQL, MySQL no permite especificar las columnas
        de conflicto directamente en la sentencia. Se basa implícitamente en las
        claves primarias y únicas de la tabla de destino.
        """
        self.logger.info(f"  -> Construyendo sentencia UPSERT para MySQL (Acción: {action.upper()})...")
        
        # MySQL usa backticks (`) para citar identificadores, no comillas dobles.
        cols_quoted = [f'`{col}`' for col in all_columns]
        cols_str = ", ".join(cols_quoted)

        # La sentencia base es un INSERT ... SELECT
        base_sql = f"INSERT INTO {target_table} ({cols_str}) SELECT {cols_str} FROM {temp_table}"

        if action.upper() == 'UPDATE':
            # Construir la cláusula 'ON DUPLICATE KEY UPDATE'.
            # Se actualizan todas las columnas EXCEPTO las que definen el conflicto.
            update_cols = [
                f"{cq} = VALUES({cq})" for cq in cols_quoted 
                if cq.strip('`') not in conflict_columns
            ]
            
            # Si no hay columnas que actualizar (solo claves), se convierte en un INSERT IGNORE.
            if not update_cols:
                return f"INSERT IGNORE {base_sql.replace('INSERT INTO', '')};"

            update_clause = f"ON DUPLICATE KEY UPDATE {', '.join(update_cols)}"
            return f"{base_sql} {update_clause};"
        
        else: # 'NOTHING'
            # Para la acción 'NOTHING', simplemente usamos INSERT IGNORE.
            return f"INSERT IGNORE {base_sql.replace('INSERT INTO', '')};"


# REEMPLAZAR/AÑADIR ESTE MÉTODO EN TU CLASE Mirror

    # ...existing code...
    # Método deploy_etl_functions migrado a AlquimistaPostgresBootstrapper
    # ...existing code...


