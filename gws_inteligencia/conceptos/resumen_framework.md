# Resumen del Framework

Este documento resume la arquitectura del framework Shekina/Aleya y sus ejecutores (Mirror, Daath, Alchemist). Se sincronizará con Google Docs/Sheets mediante BackendGSuite.

- Orquestación: Shekina
- Utilidades de flujo: Aleya
- Ejecutores: Mirror (datos crudos), Daath (grafo salud), Alchemist (transmutación)

Secciones sugeridas:
1. Visión general
2. Clases y métodos expuestos
3. Flujos (flowelt_*)
4. Estrategia de datos (raw → std_cols → std_vlrs → upsert_plan)
