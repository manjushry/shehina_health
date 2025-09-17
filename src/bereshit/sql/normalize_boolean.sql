/*********************************************************************************
 * FUNCIÓN DE NORMALIZACIÓN: fn.normalize_boolean (Versión Final, Sintaxis Corregida)
 *
 * LÓGICA:
 *  - Usa LANGUAGE sql por eficiencia.
 *  - Utiliza la sintaxis correcta 'CASE WHEN [expresión] IN ([lista])' para
 *    evaluar si el valor está dentro de un conjunto de sinónimos.
 *  - Esta es la forma idiomática y correcta en SQL.
 *********************************************************************************/
CREATE OR REPLACE FUNCTION fn.normalize_boolean(p_raw_text TEXT)
RETURNS BOOLEAN AS $$
    SELECT CASE
        WHEN lower(trim(p_raw_text)) IN ('true', 't', 'y', 'yes', 'on', '1', 'verdadero', 'si') THEN true
        WHEN lower(trim(p_raw_text)) IN ('false', 'f', 'n', 'no', 'off', '0', 'falso') THEN false
        ELSE NULL
    END;
$$ LANGUAGE sql IMMUTABLE;