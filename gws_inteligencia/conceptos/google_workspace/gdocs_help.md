# Google Docs API: Tabs (pestañas) y estructura

Esta guía resume la funcionalidad de "document tabs" en Google Docs y cómo la expone la API.

Fuentes oficiales:
- Work with tabs (Docs API): https://developers.google.com/workspace/docs/api/how-tos/tabs (Última actualización: 2025-08-28)
- Structure of a Google Docs document: https://developers.google.com/workspace/docs/api/concepts/structure (Última actualización: 2025-08-28)
- Blog Workspace Updates (lanzamiento): https://workspaceupdates.googleblog.com/2024/10/tabs-in-google-docs.html
- Help Center (uso en UI): https://support.google.com/docs/answer/15499791

## Qué son las Tabs en Docs
- Una capa organizacional dentro de un documento. Un Docs puede contener múltiples tabs, cada una con título, ID y jerarquía de subtabs.
- Cada tab tiene su propio contenido (DocumentTab.body). La API ya no recomienda acceder a `document.body` para todos los contenidos.

## Acceso vía API
- Document.tabs: lista de Tab.
- Tab.tabProperties: incluye ID (tabId), título y orden.
- Tab.childTabs: jerarquía de subtabs.
- Tab.documentTab: expone el contenido (Body) específico de esa tab.
- documents.get tiene el parámetro `includeTabsContent`:
  - true: retorna Document.tabs poblado (document.body vacío).
  - omitido/false: expone solo contenido de la primera tab en los campos legacy (document.body).
- document.batchUpdate: la mayoría de requests aceptan `tabId` para aplicar cambios a una tab específica.

## Patrones comunes
- Leer todo el contenido: setIncludeTabsContent(true), recorrer jerarquía de tabs y usar documentTab.body.
- Actualizar sólo la primera tab: obtener su tabId y dirigir las requests (InsertTextRequest, etc.) a ese tabId.
- Enlaces internos: ahora se exponen con objetos BookmarkLink/HeadingLink que incluyen tabId; `link.tabId` permite enlaces directos a tabs.

## Recomendaciones de diseño
- Si el flujo requiere “pestañas” conceptuales, use Tabs nativas y `tabId` en requests.
- Para compatibilidad con contenidos antiguos, considere plantillas y migración gradual.
- Evite depender de `document.body` si hay múltiples tabs.

## Nota sobre la UI
- La UI muestra “Pestañas del documento” en el panel izquierdo; se soportan subtabs (hasta 3 niveles).
- Se pueden copiar enlaces a tabs específicas desde la UI.

## Próximos pasos en el repo
- Implementar en BackendGSuite:
  - gdoc_list_tabs(document_id) → recorrer Document.tabs.
  - gdoc_upsert_tab(document_id, tab_name, md_text) → localizar/crear tab y aplicar requests con tabId.
  - gdoc_extract_tab(document_id, tab_name) → leer DocumentTab.body y convertir a MD (aproximado).
- Actualizar `gsuite_format` para manejar MD por tab y construir requests con tabId.