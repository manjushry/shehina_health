-- #############################################################################
-- ## Función:       fn.normalize_phone
-- ## Versión:       2.0 (Estandarizada)
-- ## Descripción:   Normaliza y valida números de teléfono de Colombia. Limpia
-- ##                caracteres no numéricos, valida celulares de 10 dígitos (3xx)
-- ##                y fijos de 10 dígitos (60x). Para fijos de 7 dígitos,
-- ##                intenta completarlos con el indicativo DANE si se provee.
-- #############################################################################
CREATE OR REPLACE FUNCTION fn.normalize_phone(
    p_phone_text TEXT,
    p_dpto_code TEXT DEFAULT NULL -- Código DANE del departamento
)
RETURNS TEXT AS $$
DECLARE
    v_cleaned_phone TEXT;
    v_indicativo TEXT;
BEGIN
    -- 1. Pre-limpieza
    IF p_phone_text IS NULL OR TRIM(p_phone_text) = '' THEN
        RETURN NULL;
    END IF;

    -- 2. Limpieza de caracteres: Dejar solo los dígitos.
    v_cleaned_phone := regexp_replace(p_phone_text, '[^0-9]', '', 'g');

    -- 3. Lógica de validación por longitud
    IF length(v_cleaned_phone) = 10 THEN
        IF v_cleaned_phone LIKE '3%' OR v_cleaned_phone LIKE '60%' THEN
            RETURN v_cleaned_phone; -- Celular o Fijo de 10 dígitos válido
        END IF;
        RETURN NULL; -- 10 dígitos, pero formato incorrecto
    ELSIF length(v_cleaned_phone) = 7 THEN
        IF p_dpto_code IS NULL THEN
            RETURN NULL; -- Incompleto, no se puede inferir
        END IF;
        -- Búsqueda del indicativo
        SELECT indicativo INTO v_indicativo FROM ref.indicativos_dane WHERE codigo_dane = p_dpto_code;
        IF v_indicativo IS NOT NULL THEN
            RETURN v_indicativo || v_cleaned_phone;
        ELSE
            RETURN NULL; -- Código DANE no encontrado
        END IF;
    ELSE
        RETURN NULL; -- Cualquier otra longitud es inválida.
    END IF;
END;
$$ LANGUAGE plpgsql STABLE;

-- Añadimos la documentación a la base de datos
COMMENT ON FUNCTION fn.normalize_phone(TEXT, TEXT) IS
'Versión: 2.0. Valida y normaliza teléfonos de Colombia (fijos y celulares). Puede completar fijos de 7 dígitos usando un código DANE.';