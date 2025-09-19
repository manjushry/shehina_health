import pandas as pd
from src.shekina.shekina import Shekina
from src.daath.daath_graph import DaathGraph

def test_missing_dataframe_logs_warning(caplog):
    config = {'db_params': {'host': 'localhost', 'user': 'u', 'password': 'p', 'dbname': 'x'}}
    shek = Shekina(config)
    shek.daath = DaathGraph()

    config_df = pd.DataFrame([
        {
            'process_key': 'p1',
            'execute': True,
            'nodes_config': [{'type': 'CUPS', 'id_field': 'cups'}],
            'edges_config': []
        }
    ])

    data_dict = {}  # Falta df para 'p1'

    with caplog.at_level('WARNING'):
        shek.populate_graph_from_config_table(config_df, data_dict)
        assert any('No hay datos para el proceso p1' in rec.message for rec in caplog.records)
