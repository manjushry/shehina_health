/*********************************************************************************
 * FUNCIÓN DE NORMALIZACIÓN UNIVERSAL: fn.normalize_array v3.0
 *
 * TAREA: Convierte una cadena de texto a un array de texto (`TEXT[]`) de forma
 *        extremadamente robusta, usando una estrategia de múltiples pasos.
 *
 * LÓGICA DE MÚLTIPLES PASOS:
 *  1. (Plan A) Intenta una conversión directa (CAST) para formatos canónicos de PG.
 *  2. (Plan B) Si falla, intenta interpretar la cadena como un array JSON.
 *  3. (Plan C) Si falla, recurre a una limpieza agresiva con expresiones regulares.
 *  4. (Último Recurso) Si todo falla, registra el error en `fn.etl_errors` y
 *     devuelve un "array de error" especial para una fácil identificación.
 *********************************************************************************/
DROP FUNCTION IF EXISTS fn.normalize_array(text);
CREATE OR REPLACE FUNCTION fn.normalize_array(
    p_raw_list_text TEXT
)
RETURNS TEXT[] AS $$
DECLARE
    v_error_id BIGINT;
BEGIN
    -- Guardia inicial para nulos o vacíos
    IF p_raw_list_text IS NULL OR trim(p_raw_list_text) = '' THEN
        RETURN ARRAY[]::TEXT[];
    END IF;

    -- --- PLAN A: Intento de CAST directo (el más rápido) ---
    BEGIN
        RETURN p_raw_list_text::TEXT[];
    EXCEPTION
        WHEN invalid_text_representation THEN
            RAISE NOTICE 'Plan A (CAST) falló para "%". Intentando Plan B (JSON).', p_raw_list_text;
            -- Si falla, la ejecución continúa al siguiente bloque
    END;

    -- --- PLAN B: Intento de conversión desde un array JSON ---
    BEGIN
        RETURN (SELECT array_agg(value) FROM jsonb_array_elements_text(p_raw_list_text::jsonb));
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Plan B (JSON) falló para "%". Intentando Plan C (Regex).', p_raw_list_text;
            -- Si falla, la ejecución continúa al siguiente bloque
    END;

    -- --- PLAN C: Limpieza agresiva con Regex ---
    BEGIN
        RETURN (
            WITH step1 AS (
                SELECT regexp_replace(p_raw_list_text, '[\[\]{}''"]', '', 'g') AS cleaned_text
            ), step2 AS (
                SELECT trim(fn.normalize_identifier(element)) AS final_element
                FROM step1, regexp_split_to_table(cleaned_text, ',') AS element
            )
            SELECT array_agg(final_element)
            FROM step2
            WHERE final_element <> ''
        );
    EXCEPTION
        WHEN OTHERS THEN
            -- --- ÚLTIMO RECURSO: Registrar error y devolver bandera ---
            RAISE WARNING 'Todos los planes de normalización fallaron para el valor: "%". Registrando en etl_errors.', p_raw_list_text;

            INSERT INTO fn.etl_errors (target_schema, target_table, target_column, row_identifier, original_value, error_message)
            VALUES ('fn.normalize_array', 'N/A', 'N/A', 'N/A', p_raw_list_text, 'Valor no convertible a TEXT[] por ningún método.')
            RETURNING error_id INTO v_error_id;

            -- Devolver el "array de error" especial que solicitaste
            RETURN ARRAY[
                format('{"error":"no_convertido", "valor":"%s", "etl_error_id":"%s"}',
                       replace(p_raw_list_text, '"', '\"'), -- Escapar comillas para el formato
                       v_error_id)
            ]::TEXT[];
    END;

END;
$$ LANGUAGE plpgsql;