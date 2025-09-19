---
sidebar_position: 1
title: Diseño del Sistema
---

import AttachMermaidLinks from '@site/src/components/AttachMermaidLinks';

Esta sección detalla la arquitectura y el diseño técnico del ecosistema de Shekina.

## Diagrama de relaciones de clases

El siguiente diagrama ilustra las relaciones entre las clases principales del sistema.

```mermaid
classDiagram
    %% Diagrama de clases y relaciones principales
    Aleya <|-- BereshitSQL
    Aleya <|-- DaathGraph
    Shekina *-- DaathGraph : inicializa
    Shekina *-- BereshitSQL : inicializa
    Shekina ..> AlchemistPrime : orquesta
    Shekina ..> Mirror : orquesta

    class Aleya {
        <<Base>>
        +set_config()
        +get_config()
        +load_from_db()
        +get_instance()
    }
    class AlchemistPrime {
        +transmute()
        +to_pandas()
    }
    class Mirror {
        +read_sql()
        +upsert_dataframe()
    }
    class Shekina {
        +run_process_sql()
        +run_bootstrap()
    }

    %% Nota: se evita la interactividad nativa de Mermaid (click) por estabilidad.
```

## Componentes principales

| Componente        | Descripción                                                                 | Enlace a documentación |
|-------------------|-----------------------------------------------------------------------------|------------------------|
| **Shekina**       | Orquestador central que inicializa y coordina los demás componentes.         | [Ver detalles](Shekina/index.md) |
| **Aleya**         | Clase base para gestión de datos y configuraciones.                          | [Ver detalles](Aleya/index.md) |
| **BereshitSQL**   | Inicialización y gestión de bases de datos, ejecutando scripts SQL.          | [Ver detalles](BereshitSQL/index.md) |
| **DaathGraph**    | Gestión del grafo de conocimiento, creación y consulta de nodos/aristas.     | [Ver detalles](DaathGraph/index.md) |
| **AlchemistPrime**| Motor ETL para transformación y limpieza de datos basada en pipelines.       | [Ver detalles](AlchemistPrime/index.md) |
| **Mirror**        | API robusta para interactuar con múltiples bases de datos.                   | [Ver detalles](Mirror/index.md) |

Cada enlace lleva a la especificación, ejemplos de uso y versionado de la clase correspondiente.
