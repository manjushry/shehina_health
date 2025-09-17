-- #############################################################################
-- ## Función:       fn.normalize_email
-- ## Versión:       2.0.1 (Mejorada, robusta, idempotente)
-- ## Fecha:         2025-09-14
-- ## Descripción:   Limpia, normaliza y valida emails. Corrige errores comunes de dominio.
-- ## Dependencias:  ninguna
-- #############################################################################

CREATE OR REPLACE FUNCTION fn.normalize_email(p_email_text TEXT)
RETURNS TEXT AS $$
DECLARE
    v_cleaned_email TEXT;
BEGIN
    IF p_email_text IS NULL OR trim(p_email_text) = '' THEN
        RETURN NULL;
    END IF;
    v_cleaned_email := lower(trim(p_email_text));
    IF v_cleaned_email IN ('-', '0', 'na', 'n/a', 'no aplica', 'no tiene', 'notiene', 'no registra', 'noregistra', '@', '#xl_eval_error#')
       OR v_cleaned_email ~ '^[0-9\s\(\)\+]{7,}$' THEN
        RETURN NULL;
    END IF;
    v_cleaned_email := regexp_replace(v_cleaned_email, '@gmil\.com$', '@gmail.com', 'i');
    v_cleaned_email := regexp_replace(v_cleaned_email, '@hotmal\.com$', '@hotmail.com', 'i');
    v_cleaned_email := regexp_replace(v_cleaned_email, '@homail\.com$', '@hotmail.com', 'i');
    v_cleaned_email := regexp_replace(v_cleaned_email, '@outlook\.es$', '@outlook.com', 'i');
    v_cleaned_email := regexp_replace(v_cleaned_email, '\.con$', '.com', 'i');
    v_cleaned_email := regexp_replace(v_cleaned_email, '@hotmail$', '@hotmail.com', 'i');
    v_cleaned_email := regexp_replace(v_cleaned_email, '\s', '', 'g');
    IF v_cleaned_email ~* '^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$' THEN
        RETURN v_cleaned_email;
    ELSE
        RETURN NULL;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE STRICT;

COMMENT ON FUNCTION fn.normalize_email(TEXT) IS
'Versión: 2.0.1. Limpia, corrige y valida un texto para devolver un email en formato estándar o NULL.';

-- Ejemplo de uso:
-- SELECT fn.normalize_email('usuario@hotmal.com');