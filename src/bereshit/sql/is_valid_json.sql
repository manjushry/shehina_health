-- PASO 1.2: Crear la dependencia PRIMERO (`fn.is_valid_json`)
DROP FUNCTION IF EXISTS fn.is_valid_json(text);
CREATE OR REPLACE FUNCTION fn.is_valid_json(p_text TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_text IS NULL OR trim(p_text) = '' THEN RETURN FALSE; END IF;
    PERFORM p_text::jsonb;
    RETURN TRUE;
EXCEPTION WHEN OTHERS THEN
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql IMMUTABLE;