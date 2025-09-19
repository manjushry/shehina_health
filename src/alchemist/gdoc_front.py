from __future__ import annotations

"""
Frontend de Alchemist para Google Docs (Tabs).

Responsabilidad: transformar representaciones (MD/texto/estructuras) a Requests de Docs
con `tabId` y viceversa. El IO real lo hace Mirror.BackendGSuite.
"""

from typing import Any, Dict, List, Optional

from mirror.backend_gsuite import BackendGSuite
from mirror import gsuite_format as fmt


def resolve_tab_id(backend: BackendGSuite, document_id: str, tab_name: str) -> Optional[str]:
    """Obtiene el tabId por título usando gdoc_read(includeTabsContent=True)."""
    doc = backend.gdoc_read(document_id)  # Se espera que implemente includeTabsContent=True
    tabs = doc.get("tabs") or []

    def walk(ts: List[Dict[str, Any]]) -> Optional[str]:
        for t in ts:
            props = (t.get("tabProperties") or {})
            if props.get("title") == tab_name:
                return props.get("tabId")
            child = t.get("childTabs") or []
            got = walk(child)
            if got:
                return got
        return None

    return walk(tabs)


def upsert_tab_from_md(backend: BackendGSuite, document_id: str, tab_name: str, md_text: str) -> None:
    """
    Crea/actualiza una tab por nombre con contenido Markdown simple (best-effort).
    Estrategia: resolver tabId y emitir InsertText con tabId al inicio.
    Nota: Crear la tab si no existe requerirá soporte en BackendGSuite (pendiente).
    """
    tab_id = resolve_tab_id(backend, document_id, tab_name)
    if not tab_id:
        # TODO: backend.gdoc_create_tab(document_id, tab_name) → nuevo tabId
        raise NotImplementedError("Crear tab no implementado en BackendGSuite")

    requests = fmt.md_to_gdoc_requests_with_tab(md_text, tab_id)
    backend.gdoc_batch_update(document_id, requests)


def extract_tab_to_md(backend: BackendGSuite, document_id: str, tab_name: str) -> str:
    """Extrae contenido de la tab como Markdown (aproximado)."""
    tab_id = resolve_tab_id(backend, document_id, tab_name)
    if not tab_id:
        raise ValueError(f"Tab no encontrada: {tab_name}")

    # TODO: backend.gdoc_extract_tab(document_id, tab_name) → MD
    # Por ahora usamos el cuerpo plano como texto, sin estilo.
    doc = backend.gdoc_read(document_id)
    for t in doc.get("tabs", []):
        props = t.get("tabProperties", {})
        if props.get("tabId") == tab_id:
            body = (((t.get("documentTab") or {}).get("body") or {}).get("content"))
            # Simplificación: concatenar textRuns
            lines: List[str] = []
            if isinstance(body, list):
                for se in body:
                    para = se.get("paragraph") if isinstance(se, dict) else None
                    if not para:
                        continue
                    for pel in para.get("elements", []):
                        tr = pel.get("textRun")
                        if tr and tr.get("content"):
                            lines.append(tr["content"]) 
            return "".join(lines)
    return ""
