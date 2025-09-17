/*********************************************************************************
 * FUNCIÓN DE NORMALIZACIÓN v1.1 (Robusta, Maneja Corchetes)
 *
 * TAREA: Recibe una cadena de texto con una lista de columnas y la devuelve
 * como un array de texto limpio.
 * MEJORA: La expresión regular ahora elimina corchetes `[]` además de las
 * comillas, permitiendo que parsee correctamente la sintaxis de array JSON.
 *********************************************************************************/
DROP FUNCTION IF EXISTS fn.normalize_column_list(text);
CREATE OR REPLACE FUNCTION fn.normalize_column_list(
    p_raw_column_list TEXT
)
RETURNS TEXT[] AS $$
BEGIN
    IF p_raw_column_list IS NULL OR trim(p_raw_column_list) = '' THEN
        RETURN ARRAY[]::TEXT[];
    END IF;

    RETURN (
        WITH
        -- INICIO DE LA CORRECCIÓN v1.1 --
        step1_no_wrappers AS (
            -- Esta regex ahora elimina comillas simples, dobles Y corchetes.
            SELECT regexp_replace(p_raw_column_list, '[\[\]''"]', '', 'g') AS cleaned_text
        ),
        -- FIN DE LA CORRECCIÓN --
        step2_split_and_trim AS (
            SELECT trim(col_name) AS column_name
            FROM step1_no_wrappers,
                 regexp_split_to_table(cleaned_text, ',') AS col_name
        )
        SELECT array_agg(column_name)
        FROM step2_split_and_trim
        WHERE column_name <> ''
    );
END;
$$ LANGUAGE plpgsql;