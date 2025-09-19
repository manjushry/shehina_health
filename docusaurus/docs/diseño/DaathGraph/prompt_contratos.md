---
title: Prompt — Contratos para poblar DaathGraph
sidebar_position: 2
---

# Prompt de diseño de contratos (DaathGraph)

Objetivo: definir contratos (opcodes y payloads) para poblar el grafo desde distintas fuentes de datos y validar consultas clave (competency questions).

## Instrucciones para el modelo

- Rol: Arquitecto de datos/grafo. Diseña y valida contratos para poblar un grafo operacional/analítico.
- Contexto: Shekina orquesta una tabla canónica; Aleya ejecuta los pasos; Registry resuelve los opcodes.
- Tarea: Proponer y normalizar contratos (opcodes + payloads) y esquemas de DataFrames para nodos y aristas.
- Restricciones:
  - Idempotencia (usar claves estables).
  - Versionado o marcas temporales (created_at/updated_at) si aplica.
  - Validación estricta de payloads y columnas en DF.

## Fuentes a cubrir

1. SISPRO
   - Nodos: instituciones, sedes, servicios.
   - Aristas: institución–sede, sede–servicio.
   - Contrato sugerido:
     - `daath.create_nodes` `{ label: "Institution", key: "institution_id", props: ["name","nit","dept","mun"] }`
     - `daath.create_edges` `{ type: "HAS_SITE", from: {label:"Institution", key:"institution_id"}, to: {label:"Site", key:"site_id"} }`

2. REPS
   - Nodos: prestadores, habilitaciones.
   - Aristas: prestador–habilitación.
   - Contrato sugerido similar al anterior, con labels `Provider`, `License`.

3. Citas
   - Nodos: paciente, cita.
   - Aristas: paciente–cita, cita–prestador, cita–servicio.
   - Claves: `patient_id`, `appointment_id`.

4. Laboratorios
   - Nodos: orden, prueba.
   - Aristas: orden–prueba, prueba–paciente.
   - Claves: `order_id`, `test_id`, `patient_id`.

## Ejemplo de tabla canónica (resumen)

```json
[
  {"id":"n1","step":"nodes_inst","opcode":"daath.create_nodes","payload":{"label":"Institution","key":"institution_id","props":["name","nit","dept","mun"]},"inputs":["df_inst"],"outputs":["nodes_created"]},
  {"id":"e1","step":"edges_site","depends_on":["nodes_inst"],"opcode":"daath.create_edges","payload":{"type":"HAS_SITE","from":{"label":"Institution","key":"institution_id"},"to":{"label":"Site","key":"site_id"}},"inputs":["df_site"],"outputs":["edges_created"]}
]
```

## Competency questions (consultas)

Propón las consultas que el grafo debe responder:
- ¿Cuántas sedes por institución (SISPRO) por municipio?
- ¿Qué servicios habilitados (REPS) ofrece cada prestador y dónde?
- ¿Cuál es el lead time promedio entre cita y resultado de laboratorio por paciente?
- ¿Qué rutas de atención conectan paciente → cita → servicio → prestador → laboratorio?

## Entregables

- Especificación de contratos (opcodes + payload) por fuente.
- Esquemas de DataFrames de entrada (columnas mínimas requeridas).
- Batería de validaciones (asserts) previas a generar nodos/aristas.
- Ejemplos de tabla canónica para escenarios representativos.
