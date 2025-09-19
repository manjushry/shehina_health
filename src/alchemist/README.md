# Alchemist Frontends (GSuite)

Frontends de representación/transformación para Google Docs/Sheets/Slides.

- gdoc_front.py: MD/estructuras ↔ Requests Docs con `tabId` (Tabs nativas).
- gsheet_front.py: tablas ↔ rangos A1.
- slides_front.py: plantilla de presentaciones (futuro).

Backends (IO) están en `mirror.backend_gsuite`. Mantener esta separación minimiza
acoplamiento: si cambian las APIs o estrategias de formateo, sólo se tocan los
frontends; el IO subyacente permanece estable.

Contratos mínimos:
- gdoc_front.upsert_tab_from_md(backend, document_id, tab_name, md_text) → None
- gdoc_front.extract_tab_to_md(backend, document_id, tab_name) → str
- gsheet_front.write_table(backend, spreadsheet_id, a1_range, table) → None
- gsheet_front.read_table(backend, spreadsheet_id, a1_range) → table
- gsheet_front.ensure_sheet(backend, spreadsheet_id, title) → sheetId

Notas:
- Se requiere que BackendGSuite implemente includeTabsContent=True en gdoc_read.
- Futuros estilos/markdown ricos se mapearán gradualmente.