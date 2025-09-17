
import os
import networkx as nx
import pandas as pd
import psycopg2
import pickle
from src.aleya.aleya import Aleya


class DaathGraph(Aleya):
    """
    Grafo de conocimiento centralizado para salud, hereda de Aleya.
    Permite poblar, consultar y gestionar nodos/aristas usando métodos genéricos y específicos.

    Ejemplo de uso:
    >>> dg = DaathGraph(db_params)
    >>> dg.set_config({'param': 'valor'})
    >>> dg.set_data(pd.DataFrame(...))
    >>> dg.set_context(nx.DiGraph())
    >>> dg.add_node('CUPS', 'nodo1', 'Nombre Nodo')
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db_params=None, config_path=None, dict_path=None, graph_file=None):
        self.db_params = db_params
        if config_path:
            import yaml
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        if not hasattr(self, 'graph'):
            self.graph = nx.DiGraph()
        self._homologation_cache = {}
        if graph_file and os.path.exists(graph_file):
            self.load_from_file(graph_file)
        elif db_params:
            self.load_from_db(db_params)

    def build_uri(self, domain, type_, identifier):
        """
        Construye un URI robusto y normalizado para nodos/aristas.
        Ejemplo: urn:alchemist:sispro:CUPS:12345
        """
        norm_id = str(identifier).strip().replace(' ', '_').replace(':', '_')
        return f"urn:alchemist:{domain}:{type_}:{norm_id}"

    def populate_from_data(self, source_data_df: pd.DataFrame, nodes_config: list, edges_config: list):
        """
        Puebla el grafo a partir de un DataFrame y una configuración de nodos/aristas.
        Usa build_uri para URIs robustos y normalizados.
        """
        nodes_to_add = []
        edges_to_add = []
        for _, row in source_data_df.iterrows():
            for node_cfg in nodes_config:
                domain = node_cfg.get('domain', 'default')
                type_ = node_cfg['type']
                id_val = row[node_cfg['id_field']]
                node_id = self.build_uri(domain, type_, id_val)
                node_attrs = {
                    "type": type_,
                    "name": row.get(node_cfg.get('name_field')),
                    "uri": node_id
                }
                for attr in node_cfg.get('extra_fields', []):
                    node_attrs[attr] = row.get(attr)
                nodes_to_add.append((node_id, node_attrs))
            for edge_cfg in edges_config:
                src_domain = edge_cfg.get('source_domain', 'default')
                src_type = edge_cfg.get('source_type', 'default')
                src_id_val = row[edge_cfg['source']]
                source_id = self.build_uri(src_domain, src_type, src_id_val)
                tgt_domain = edge_cfg.get('target_domain', 'default')
                tgt_type = edge_cfg.get('target_type', 'default')
                tgt_id_val = row[edge_cfg['target']]
                target_id = self.build_uri(tgt_domain, tgt_type, tgt_id_val)
                edge_attrs = {"type": edge_cfg['relationship'], "uri": f"{source_id}->{target_id}"}
                for attr in edge_cfg.get('extra_fields', []):
                    edge_attrs[attr] = row.get(attr)
                edges_to_add.append((source_id, target_id, edge_attrs))
        self.graph.add_nodes_from(nodes_to_add)
        self.graph.add_edges_from(edges_to_add)
        import logging
        logging.info(f"Grafo actualizado: {self.graph.number_of_nodes()} nodos, {self.graph.number_of_edges()} aristas.")

    def _load_node_edge_dict(self, dict_path=None):
        import yaml
        dict_path = dict_path or os.path.join(os.path.dirname(__file__), 'daath_node_edge_dict.yml')
        with open(dict_path, 'r') as f:
            self.node_edge_dict = yaml.safe_load(f)

    def get_node_uri(self, category, code):
        prefix = self.node_edge_dict['node_categories'][category]['uri_prefix']
        return f"{prefix}{code}"

    def get_edge_uri(self, edge_type):
        return self.node_edge_dict['edge_types'][edge_type]['uri']

    def load_from_db(self, db_params):
        """Carga nodos y aristas desde PostgreSQL."""
        conn = psycopg2.connect(**db_params)
        nodes_df = pd.read_sql("SELECT node_id, node_type, name, description, properties FROM definition.kg_nodes", conn)
        edges_df = pd.read_sql("SELECT source_node_id, target_node_id, relationship_type FROM definition.kg_edges", conn)
        conn.close()
        self.graph.clear()
        for _, row in nodes_df.iterrows():
            self.graph.add_node(row['node_id'], type=row['node_type'], name=row['name'], description=row['description'], properties=row['properties'])
        for _, row in edges_df.iterrows():
            self.graph.add_edge(row['source_node_id'], row['target_node_id'], type=row['relationship_type'])
        self._homologation_cache.clear()

    def save_to_file(self, path):
        with open(path, 'wb') as f:
            pickle.dump(self.graph, f)

    def load_from_file(self, path):
        with open(path, 'rb') as f:
            self.graph = pickle.load(f)

    def update_from_knime(self, nodes_df, edges_df):
        """Permite actualizar el grafo desde KNIME (recibe DataFrames)."""
        for _, row in nodes_df.iterrows():
            self.graph.add_node(row['node_id'], type=row['node_type'], name=row['name'], description=row.get('description'), properties=row.get('properties'))
        for _, row in edges_df.iterrows():
            self.graph.add_edge(row['source_node_id'], row['target_node_id'], type=row['relationship_type'])
        self._homologation_cache.clear()

    def get_mapping_dict(self, concept_key):
        if concept_key in self._homologation_cache:
            return self._homologation_cache[concept_key]
        mapping = {}
        if self.graph.has_node(concept_key):
            for source, target, data in self.graph.in_edges(concept_key, data=True):
                if data.get('type') == 'ES_SINONIMO_DE':
                    source_name = self.graph.nodes[source].get('name', source)
                    mapping[source_name] = target
        self._homologation_cache[concept_key] = mapping
        return mapping

    def get_cups_to_service_map(self):
        mapping = {}
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'CUPS':
                for successor in self.graph.successors(node):
                    if self.graph.edges[node, successor].get('type') == 'PERTENECE_A':
                        mapping[node] = successor
                        break
        return mapping

    def recommend_new_relations(self, agent):
        """El agente inteligente puede sugerir nuevas relaciones/nodos."""
        # agent debe implementar un método .suggest_relations(graph)
        return agent.suggest_relations(self.graph)

    def query_cypher(self, cypher_query, result_columns=None):
        """Ejecuta una consulta Cypher en AGE y devuelve un DataFrame."""
        sql = f"SELECT * FROM cypher('knowledge_graph', $$ {cypher_query} $$) AS (result agtype);"
        conn = psycopg2.connect(**self.db_params)
        df = pd.read_sql(sql, conn)
        conn.close()
        if result_columns:
            return df[result_columns]
        return df

    def get_cups_by_service(self, service_id):
        """Devuelve los CUPS que pertenecen a un grupo de servicio usando Cypher en AGE."""
        cypher = f"MATCH (c:CUPS)-[:PERTENECE_A]->(g:Servicio) WHERE g.id = '{service_id}' RETURN c.codigo, c.nombre"
        return self.query_cypher(cypher, result_columns=['c.codigo', 'c.nombre'])

    def populate_from_yaml_config(self, process_name, sql_folder=None):
        # Método obsoleto eliminado
        pass

    def add_node(self, node_type, node_id, node_name=None):
        """
        Agrega un nodo al grafo. node_type: tipo de nodo, node_id: identificador único, node_name: nombre opcional.
        """
        self.graph.add_node(node_id, type=node_type, name=node_name)

    def add_edge(self, source_id, target_id, relationship_type):
        """
        Agrega una arista/relación al grafo. source_id: nodo origen, target_id: nodo destino, relationship_type: tipo de relación.
        """
        self.graph.add_edge(source_id, target_id, type=relationship_type)

    @classmethod
    def get_instance(cls, db_params=None, graph_file=None):
        """Acceso global a la instancia única."""
        if cls._instance is None:
            cls._instance = DaathGraph(db_params=db_params, graph_file=graph_file)
        return cls._instance
