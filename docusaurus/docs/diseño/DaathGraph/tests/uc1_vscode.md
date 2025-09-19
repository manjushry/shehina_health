---
title: DaathGraph · UC1 · VS Code
---

## test_id
DaathGraph/UC1

## Objetivo
Verificar que `update_from_knime` agrega nodos y aristas al grafo.

## Ejecución (pytest)
```
pytest -q tests\DaathGraph\test_daathgraph_uc1.py::test_update_from_knime
```

## Código de prueba (referencia)
Ruta: `tests/DaathGraph/test_daathgraph_uc1.py`

```python
import pandas as pd
import networkx as nx
from src.daath.daath_graph import DaathGraph


def test_update_from_knime():
    dg = DaathGraph()
    nodes_df = pd.DataFrame([
        {'node_id': 'n1', 'node_type': 'CUPS', 'name': 'Consulta'},
        {'node_id': 's1', 'node_type': 'Servicio', 'name': 'S1'},
    ])
    edges_df = pd.DataFrame([
        {'source_node_id': 'n1', 'target_node_id': 's1', 'relationship_type': 'PERTENECE_A'}
    ])

    dg.update_from_knime(nodes_df, edges_df)

    assert dg.graph.has_node('n1')
    assert dg.graph.has_edge('n1', 's1')
```
