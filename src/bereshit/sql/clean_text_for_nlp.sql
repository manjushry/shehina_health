-- #############################################################################
-- ## Función:       fn.clean_text_for_nlp
-- ## Versión:       2.3.1 (Mejorada, robusta, idempotente)
-- ## Fecha:         2025-09-14
-- ## Descripción:   Prepara texto para NLP. Limpia, normaliza y preserva la
-- ##                puntuación clave, incluyendo los signos de apertura ¿ y ¡.
-- ## Dependencias:  unaccent
-- #############################################################################
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE OR REPLACE FUNCTION fn.clean_text_for_nlp(p_input_text TEXT)
RETURNS TEXT AS $$
DECLARE
    v_cleaned_text TEXT;
BEGIN
    IF p_input_text IS NULL OR trim(p_input_text) = '' THEN
        RETURN NULL;
    END IF;
    -- 1. Convertir a minúsculas
    v_cleaned_text := lower(p_input_text);
    -- 2. Quitar acentos (requiere la extensión unaccent)
    v_cleaned_text := unaccent(v_cleaned_text);
    -- 3. Estandarizar guiones, barras y saltos de línea a un solo espacio
    v_cleaned_text := regexp_replace(v_cleaned_text, '[-/\r\n\t]+', ' ', 'g');
    -- 4. [LÓGICA CORREGIDA] Eliminamos caracteres no deseados,
    --    PERO AHORA la lista de permitidos incluye ¿ y ¡.
    v_cleaned_text := regexp_replace(v_cleaned_text, '[^a-z0-9\s.,;?!:$€()\[\]%¿¡]', '', 'g');
    -- 5. Colapsar múltiples espacios a uno solo.
    v_cleaned_text := regexp_replace(v_cleaned_text, '\s+', ' ', 'g');

    RETURN trim(v_cleaned_text);
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

COMMENT ON FUNCTION fn.clean_text_for_nlp(TEXT) IS
'Versión: 2.3.1. Limpia texto para NLP, preservando puntuación española. Idempotente y robusta.';

-- Ejemplo de uso:
-- SELECT fn.clean_text_for_nlp('¿Qué tal, amigo? ¡Bienvenido!');