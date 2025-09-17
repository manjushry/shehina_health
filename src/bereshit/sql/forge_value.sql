/*********************************************************************************
 * FUNCIÓN DESPACHADORA: fn_forge_value v1.0 (El Forjador de Valores)
 *
 * TAREA: Actúa como un controlador central para la normalización y conversión
 *        de datos. Recibe un valor de texto y un tipo de dato de destino, y
 *        despacha la tarea a la función especializada apropiada.
 *
 * RETORNO: Siempre devuelve TEXT. La conversión final al tipo de dato
 *          objetivo se realiza en la cláusula USING de la llamada.
 *********************************************************************************/
DROP FUNCTION IF EXISTS fn.forge_value(text, text);
CREATE OR REPLACE FUNCTION fn.forge_value(
    p_value TEXT,
    p_target_type TEXT
)
RETURNS TEXT AS $$
DECLARE
    v_cleaned_type TEXT := lower(trim(p_target_type));
BEGIN
    -- El despachador CASE que llama a la herramienta correcta
    RETURN CASE v_cleaned_type
        WHEN 'boolean' THEN (fn.normalize_boolean(p_value))::text
        WHEN 'text[]'  THEN (fn.normalize_array(p_value))::text
        WHEN 'jsonb'   THEN (fn.forge_json(p_value))::text
        -- Por defecto, si no hay regla especial, devuelve el valor tal cual
        -- para que el CAST directo intente la conversión.
        ELSE p_value
    END;
END;
$$ LANGUAGE plpgsql;