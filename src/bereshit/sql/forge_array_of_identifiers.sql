/*********************************************************************************
FUNCIÓN FORJADORA: fn.forge_array_of_identifiers
TAREA: Toma un array de texto y estandariza cada uno de sus elementos a un
formato de identificador limpio y de máquina.

LÓGICA:
Descompone el array de entrada en una tabla de filas individuales (unnest).
Aplica la función fn.normalize_identifier a cada fila/elemento.
Filtra cualquier elemento que se haya convertido en nulo o vacío.
Recompone los elementos limpios en un nuevo array de salida (array_agg).
Este enfoque set-based (basado en conjuntos) es más eficiente que un bucle.

EJEMPLO DE USO:
SELECT fn.forge_array_of_identifiers(ARRAY[' Correo Electrónico ', 'TELÉFONO', null, 'Código Postal']);
-- Devuelve: ARRAY['correo_electronico', 'telefono', 'codigo_postal']
*********************************************************************************/
CREATE OR REPLACE FUNCTION fn.forge_array_of_identifiers(
p_raw_array TEXT[]
)
RETURNS TEXT[] AS 

BEGIN
-- Guardia inicial: si el array es nulo o está vacío, devolver un array vacío.
IF p_raw_array IS NULL OR cardinality(p_raw_array) = 0 THEN
RETURN ARRAY[]::TEXT[];
END IF;
Generated code
RETURN (
    SELECT array_agg(clean_identifier)
    FROM (
        -- Primero, desanidamos el array y aplicamos la limpieza a cada elemento.
        SELECT fn.normalize_identifier(element) AS clean_identifier
        FROM unnest(p_raw_array) AS u(element)
    ) AS subquery
    -- Importante: Solo nos quedamos con los identificadores que no son nulos ni vacíos.
    WHERE clean_identifier IS NOT NULL AND clean_identifier <> ''
);
Use code with caution.
END;
 LANGUAGE plpgsql IMMUTABLE;