-- Herramienta para JSONB
DROP FUNCTION IF EXISTS fn.forge_json(text);
CREATE OR REPLACE FUNCTION fn.forge_json(p_raw_text TEXT)
RETURNS JSONB AS $$
BEGIN
    RETURN p_raw_text::jsonb;
EXCEPTION
    WHEN others THEN RETURN NULL;
END;
$$ LANGUAGE plpgsql IMMUTABLE;