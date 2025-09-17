
# Clase principal para integración KNIME
import os
from src.daath.daath_graph import DaathGraph
from src.bereshit.bereshit_sql import BereshitSQL

class Shekina:
    """
    Orquestador principal entre KNIME y el ecosistema Python/DB.
    Gestiona contextos simples (config, datos, grafos) y complejos (DaathGraph, BereshitSQL, AlchemistPrime).

    Ejemplo de uso:
    >>> shek = Shekina(config)
    >>> shek.set_config({'param': 'valor'})
    >>> shek.daath = DaathGraph(config['daath'])
    >>> shek.bereshit = BereshitSQL(config['bereshit'])
    >>> shek.run_process_key('sispro_cups_grservicios')
    """
    def run_process_sql(self, process_key):
        """
        Ejecuta el script SQL asociado a un proceso y pobla el grafo si corresponde.
        """
        if not self.bereshit:
            self.init_bereshit()
        process_row = None
        if self.process_table is not None:
            for row in self.process_table:
                if row['process_key'] == process_key and row.get('execute', True):
                    process_row = row
                    break
        if not process_row:
            raise ValueError(f"Proceso '{process_key}' no encontrado o no ejecutable.")
        sql = process_row['source_query']
        results_df = self.bereshit.fetch_dataframe(sql)
        if self.daath and results_df is not None and not results_df.empty:
            self.daath.populate_from_data(
                results_df,
                process_row['nodes_config'],
                process_row['edges_config']
            )
    def populate_graph_from_config_table(self, config_df, data_dict):
        """
        Itera sobre la tabla de configuración recibida desde KNIME.
        data_dict: {process_key: DataFrame de datos}
        """
        import logging
        if not self.daath:
            self.init_daath()
        for _, config_row in config_df.iterrows():
            if not config_row.get('execute', True):
                continue
            process_key = config_row['process_key']
            nodes_config = config_row['nodes_config']
            edges_config = config_row['edges_config']
            source_data_df = data_dict.get(process_key)
            if source_data_df is None or source_data_df.empty:
                logging.warning(f"No hay datos para el proceso {process_key}")
                continue
            try:
                self.daath.populate_from_data(source_data_df, nodes_config, edges_config)
                logging.info(f"Proceso {process_key} ejecutado correctamente.")
            except Exception as e:
                logging.error(f"Error en proceso {process_key}: {e}")
    """
    Clase central para gestionar el entorno, grafo de conocimiento y scripts expertos en KNIME.
    Inicializa componentes y expone métodos para cada proceso.
    """
    def __init__(self, config, process_table=None):
        """
        Inicializa Shekina con configuración y opcionalmente una tabla de procesos/configuración.
        """
        self.config = config
        self.process_table = process_table
        self.daath = None
        self.bereshit = None

    def init_daath(self):
        self.daath = DaathGraph(db_params=self.config['db_params'])

    def init_bereshit(self):
        sql_dir = self.config.get('sql_dir', os.path.join(os.path.dirname(__file__), '..', 'alchemist', 'bereshit_sql'))
        self.bereshit = BereshitSQL(self.config['db_params'], db_type='postgresql', sql_dir=sql_dir)

    def run_bootstrap(self):
        if not self.bereshit:
            self.init_bereshit()
        self.bereshit.bootstrap()

    def run_etl(self):
        # Aquí puedes llamar a otros procesos ETL
        pass

    def query_grafo(self, cypher_query):
        if not self.daath:
            self.init_daath()
        return self.daath.query_cypher(cypher_query)

    # ...otros métodos expertos para KNIME...

