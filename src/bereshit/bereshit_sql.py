import logging
import os
import glob
from src.aleya.aleya import Aleya

class BereshitSQL(Aleya):
    """
    Clase para gestión y normalización ETL en bases de datos, hereda de Alchemist.
    Permite conectar, ejecutar SQL y gestionar contexto de datos/tablas.

    Ejemplo de uso:
    >>> bsql = BereshitSQL(db_config)
    >>> bsql.set_config({'param': 'valor'})
    >>> bsql.connect()
    >>> bsql.execute_sql('SELECT ...')
    """
    """
    Clase inspiradora para bootstrap ETL y normalización en bases de datos.
    Permite activar extensiones, schemas y funciones en PostgreSQL (por ahora).
    Recibe datos de conexión y tipo de base de datos en el constructor.
    Uso:
        db_config = {...}
        bereshit = BereshitSQL(db_config, db_type='postgresql', sql_dir='...')
        bereshit.bootstrap()
    """
    def __init__(self, db_config, db_type='postgresql', sql_dir=None, custom_search_path='public, dwh, fn'):
        self.db_config = db_config
        self.db_type = db_type.lower()
        self.sql_dir = sql_dir
        self.custom_search_path = custom_search_path
        self.logger = logging.getLogger('BereshitSQL')
        self.conn = None

    def connect(self):
        if self.db_type == 'postgresql':
            import psycopg2
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = True
        else:
            raise NotImplementedError(f"Bootstrap solo implementado para PostgreSQL. Solicitado: {self.db_type}")

    def close(self):
        if self.conn:
            self.conn.close()

    def execute_sql(self, sql, params=None):
        """
        Ejecuta SQL con parámetros opcionales.
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, params or ())
            self.logger.info("SQL ejecutado correctamente.")
        except Exception as e:
            self.logger.error(f"Error ejecutando SQL: {e}")
            raise

    def fetch_dataframe(self, query, params=None):
        """
        Devuelve un DataFrame, con parámetros opcionales.
        """
        try:
            import pandas as pd
            df = pd.read_sql_query(query, self.conn, params=params)
            self.logger.info(f"Consulta ejecutada, {len(df)} filas obtenidas.")
            return df
        except Exception as e:
            self.logger.error(f"Error al ejecutar fetch: {e}")
            return pd.DataFrame()

    def run_bootstrap_scripts(self):
        # Ejecuta los scripts independientes en orden lógico
        base_dir = self.sql_dir or os.path.dirname(__file__)
        for script_name in [
            'activate_extensions.sql',
            'activate_schemas.sql',
            'activate_tables.sql'
        ]:
            script_path = os.path.join(base_dir, script_name)
            if os.path.exists(script_path):
                with open(script_path, 'r', encoding='utf-8') as f:
                    sql_code = f.read()
                    try:
                        self.execute_sql(sql_code)
                        self.logger.info(f"[OK] Ejecutado: {script_name}")
                    except Exception as e:
                        self.logger.error(f"[ERROR] en {script_name}: {e}")

    def deploy_functions(self):
        if self.db_type == 'postgresql':
            self.logger.info("Desplegando funciones ETL y normalización...")
            self.run_bootstrap_scripts()
            # Ejecutar todos los archivos SQL de funciones/utilidades
            if self.sql_dir:
                for sql_file in sorted(glob.glob(os.path.join(self.sql_dir, '*.sql'))):
                    # Evitar duplicar los scripts de bootstrap
                    if os.path.basename(sql_file) in [
                        'activate_extensions.sql',
                        'activate_schemas.sql',
                        'activate_tables.sql'
                    ]:
                        continue
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        sql_code = f.read()
                        try:
                            self.execute_sql(sql_code)
                            self.logger.info(f"[OK] Ejecutado: {os.path.basename(sql_file)}")
                        except Exception as e:
                            self.logger.error(f"[ERROR] en {sql_file}: {e}")
            # Establecer search_path
            self.execute_sql(f"SET search_path TO {self.custom_search_path};")
            self.logger.info(f"[OK] search_path establecido en '{self.custom_search_path}'")

    def bootstrap(self):
        try:
            self.connect()
            self.deploy_functions()
        finally:
            self.close()
