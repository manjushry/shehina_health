# Jerarquía de Clases

Esta sección documenta la jerarquía y relaciones entre las clases principales del framework Shekina.

## Diagrama de herencia y composición

```mermaid
classDiagram
    class Aleya {
        +config
        +data
        +context
        +set_config()
        +get_config()
        +set_data()
        +get_data()
        +set_context()
        +get_context()
    }
    class Daath {
        +build_uri()
        +populate_from_data()
    }
    class Bereshit {
        +connect()
        +execute_sql()
        +fetch_dataframe()
    }
    class Mirror {
        +read_sql()
        +prepare_dataframe()
        +upsert_dataframe()
        +update_from_dataframe()
    }
    class Prime {
        +transmute()
        +agregar_status_y_errores()
        +limpiar_columnas_intermedias()
    }
    class Shekina {
        +run_process_key()
        +run_process_sql()
    }

    Aleya <|-- Daath
    Aleya <|-- Bereshit
    Aleya <|-- Mirror
    Shekina o-- Daath
    Shekina o-- Bereshit
    Shekina o-- Prime
```

## Descripción de la jerarquía
- `Aleya`: Clase base para configuración y contexto.
- `Daath`, `Bereshit`, `Mirror`: Heredan de Aleya, especializadas en grafo, persistencia y manipulación de datos.
- `Prime`: Procesos avanzados y utilidades.
- `Shekina`: Orquestador principal, compone y coordina las clases especializadas.

---

La validación progresiva se realizará siguiendo las épicas definidas.