-- #############################################################################
-- ## Función:       fn.normalize_identifier
-- ## Versión:       2.1 (Lógica de reemplazo corregida)
-- ## Descripción:   Crea un identificador de máquina limpio y estandarizado a
-- ##                partir de un texto. Ideal para nombres de columnas,
-- ##                claves de búsqueda normalizadas, o valores de categorías.
-- #############################################################################
CREATE OR REPLACE FUNCTION fn.normalize_identifier(p_input_text TEXT)
RETURNS TEXT AS $$
DECLARE
    v_normalized_text TEXT;
BEGIN
    IF p_input_text IS NULL OR TRIM(p_input_text) = '' THEN
        RETURN NULL;
    END IF;

    -- 1. Convertir a minúsculas
    v_normalized_text := lower(p_input_text);
    -- 2. Manejar caracteres especiales del español
    v_normalized_text := replace(v_normalized_text, 'ñ', 'ni');
    v_normalized_text := translate(v_normalized_text, 'áéíóú', 'aeiou');
    -- 3. Reemplazar ' de ' y guiones por guion bajo
    v_normalized_text := regexp_replace(v_normalized_text, '\s+de\s+|-', '_', 'g');
    -- 4. Reemplazar CUALQUIER espacio restante por un guion bajo
    v_normalized_text := regexp_replace(v_normalized_text, '\s', '_', 'g');
    -- 5. Eliminar cualquier caracter que no sea letra, número o guion bajo
    v_normalized_text := regexp_replace(v_normalized_text, '[^a-z0-9_]', '', 'g');
    -- 6. Colapsar múltiples guiones bajos seguidos por uno solo
    v_normalized_text := regexp_replace(v_normalized_text, '_+', '_', 'g');
    -- 7. Quitar guiones bajos al inicio y al final
    v_normalized_text := trim(v_normalized_text, '_');

    RETURN v_normalized_text;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Añadimos la documentación a la base de datos
COMMENT ON FUNCTION fn.normalize_identifier(TEXT) IS
'Versión: 2.1. Crea un identificador de máquina limpio (minúsculas, sin acentos, solo guiones bajos). Preserva guiones bajos originales.';