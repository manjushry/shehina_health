import pandas as pd
from src.shekina.shekina import Shekina
from src.daath.daath_graph import DaathGraph

def test_skip_execute_false():
    config = {'db_params': {'host': 'localhost', 'user': 'u', 'password': 'p', 'dbname': 'x'}}
    shek = Shekina(config)
    shek.daath = DaathGraph()

    config_df = pd.DataFrame([
        {
            'process_key': 'p1',
            'execute': False,
            'nodes_config': [{'type': 'CUPS', 'id_field': 'cups'}],
            'edges_config': []
        }
    ])

    data_dict = {'p1': pd.DataFrame([{'cups': '001'}])}

    before_nodes = shek.daath.graph.number_of_nodes()
    shek.populate_graph_from_config_table(config_df, data_dict)
    after_nodes = shek.daath.graph.number_of_nodes()

    assert before_nodes == after_nodes, "No debe crear nodos para execute=false"
