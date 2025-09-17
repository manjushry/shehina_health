-- #############################################################################
-- ## Función:       fn.normalize_text
-- ## Versión:       2.0 (Estandarizada)
-- ## Descripción:   Convierte una cadena de texto a un formato normalizado y
-- ##                limpio: minúsculas, sin acentos, sin 'ñ', sin caracteres
-- ##                especiales y con guiones bajos como único separador.
-- #############################################################################
CREATE OR REPLACE FUNCTION fn.normalize_text(p_input_text TEXT)
RETURNS TEXT AS $$
DECLARE
    v_normalized_text TEXT;
BEGIN
    IF p_input_text IS NULL THEN
        RETURN NULL;
    END IF;

    -- 1. Convertir a minúsculas
    v_normalized_text := lower(p_input_text);
    -- 2. Reemplazar 'ñ' por 'ni'
    v_normalized_text := replace(v_normalized_text, 'ñ', 'ni');
    -- 3. Quitar acentos de las vocales
    v_normalized_text := translate(v_normalized_text, 'áéíóú', 'aeiou');
    -- 4. Reemplazar espacios, ' de ' y guiones por un solo guion bajo
    v_normalized_text := regexp_replace(v_normalized_text, '(\s+de\s+|\s+|-)', '_', 'g');
    -- 5. Eliminar cualquier caracter que no sea letra, número o guion bajo
    v_normalized_text := regexp_replace(v_normalized_text, '[^a-z0-9_]', '', 'g');
    -- 6. Reemplazar múltiples guiones bajos seguidos por uno solo
    v_normalized_text := regexp_replace(v_normalized_text, '_+', '_', 'g');
    -- 7. Quitar guiones bajos al inicio y al final
    v_normalized_text := trim(v_normalized_text, '_');

    RETURN v_normalized_text;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Añadimos la documentación a la base de datos
COMMENT ON FUNCTION fn.normalize_text(TEXT) IS
'Versión: 2.0. Convierte un texto a un formato limpio: minúsculas, sin acentos/ñ, y usando guiones bajos como separador.';