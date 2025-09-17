# BereshitSQL

Clase para gestión y normalización ETL en bases de datos.

## Estructura recomendada
- `bereshit_sql.py`: Clase principal para conexión y operaciones SQL.
- `sql/`: Carpeta centralizada para todos los archivos `.sql` (bootstrap, funciones, utilidades).

## Uso de scripts SQL
Coloca todos los archivos SQL en `src/bereshit/sql/`. La clase BereshitSQL buscará y ejecutará los scripts desde esta carpeta, permitiendo una gestión ordenada y reutilizable.

## Ejemplo de inicialización
```python
from bereshit.bereshit_sql import BereshitSQL
bsql = BereshitSQL(db_config, db_type='postgresql', sql_dir='src/bereshit/sql')
bsql.bootstrap()
```

## Ventajas
- Mantenibilidad y control de versiones
- Reusabilidad de scripts
- Organización clara entre código y recursos
- Escalabilidad para nuevos scripts y bases de datos

---
Para más detalles, consulta la wiki y el README del módulo.