-- #############################################################################
-- ## Función:       fn.create_fhir_contactpoints
-- ## Versión:       2.0 (Estandarizada)
-- ## Descripción:   Toma una o más cadenas de texto (que pueden contener
-- ##                múltiples emails o teléfonos separados por comas), los
-- ##                valida y los estructura en un array JSONB de objetos
-- ##                ContactPoint, siguiendo un formato inspirado en FHIR.
-- #############################################################################
CREATE OR REPLACE FUNCTION fn.create_fhir_contactpoints(
    p_periodo_cargue TEXT,
    p_dpto_code TEXT,
    VARIADIC p_contact_strings TEXT[]
)
RETURNS JSONB AS $$
DECLARE
    contact_string TEXT;
    contact_value TEXT;
    cleaned_value TEXT;
    contact_point JSONB;
    contact_points_array JSONB[] := '{}';
BEGIN
    IF p_contact_strings IS NULL THEN RETURN '[]'::jsonb; END IF;

    FOREACH contact_string IN ARRAY p_contact_strings LOOP
        IF contact_string IS NULL OR TRIM(contact_string) = '' THEN CONTINUE; END IF;

        FOREACH contact_value IN ARRAY string_to_array(contact_string, ',') LOOP
            IF contact_value IS NULL OR TRIM(contact_value) = '' THEN CONTINUE; END IF;

            -- Intento 1: Validar como Email
            cleaned_value := fn.normalize_email(contact_value);
            IF cleaned_value IS NOT NULL THEN
                contact_point := jsonb_build_object('system','email','value',cleaned_value,'use','work','periodo',p_periodo_cargue);
                contact_points_array := array_append(contact_points_array, contact_point);
                CONTINUE;
            END IF;

            -- Intento 2: Validar como Teléfono
            cleaned_value := fn.normalize_phone(contact_value, p_dpto_code);
            IF cleaned_value IS NOT NULL THEN
                contact_point := jsonb_build_object('system','phone','value',cleaned_value,'use',CASE WHEN cleaned_value LIKE '3%' THEN 'mobile' ELSE 'work' END,'periodo',p_periodo_cargue);
                contact_points_array := array_append(contact_points_array, contact_point);
                CONTINUE;
            END IF;
        END LOOP;
    END LOOP;

    IF array_length(contact_points_array, 1) IS NULL THEN RETURN '[]'::jsonb; END IF;
    RETURN to_jsonb(contact_points_array);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn.create_fhir_contactpoints(TEXT, TEXT, TEXT[]) IS
'Versión: 2.0. Crea un array JSONB de ContactPoints (FHIR) a partir de cadenas de texto de contacto. Usa fn.normalize_email y fn.normalize_phone.';