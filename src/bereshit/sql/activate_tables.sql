-- #############################################################################
-- ## Script:        activate_tables.sql
-- ## Descripción:   Crea tablas utilitarias necesarias para el framework ETL
-- ## Fecha:         2025-09-14
-- #############################################################################
-- Ejemplo: tabla de errores ETL
CREATE TABLE IF NOT EXISTS fn.etl_errors (
    error_id BIGSERIAL PRIMARY KEY,
    target_schema TEXT,
    target_table TEXT,
    target_column TEXT,
    row_identifier TEXT,
    original_value TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT now()
);
