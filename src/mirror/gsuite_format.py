from __future__ import annotations

"""
Utilidades de formato para interoperar entre Markdown, Google Docs y Google Sheets.

Objetivos iniciales:
- Transformar tablas (listas de listas) a GSheet y viceversa.
- Generar requests básicos de GDoc para construir secciones (simular 'pestañas').
- Preparar marcos de conversión MD ↔ GDoc (esqueleto).
"""

from typing import Any, Dict, List


def table_to_gsheet(values: List[List[Any]]) -> List[List[Any]]:
    """Normaliza una tabla Python a valores admitidos por Sheets API."""
    return [["" if v is None else v for v in row] for row in values]


def gsheet_to_table(values: List[List[Any]]) -> List[List[Any]]:
    """Convierte valores de Sheets a una tabla Python (ya vienen como lista de listas)."""
    return values or []


def gdoc_make_section(title: str) -> Dict[str, Any]:
    """Crea un request básico para insertar un encabezado (simula pestañas por secciones)."""
    return {
        "insertText": {
            "location": {"index": 1},
            "text": f"\n# {title}\n\n"
        }
    }


def md_to_gdoc_requests(md_text: str) -> List[Dict[str, Any]]:
    """Deprecated: prefiera md_to_gdoc_requests_with_tab con tabId nativo."""
    return md_to_gdoc_requests_with_tab(md_text, tab_id=None)


def md_to_gdoc_requests_with_tab(md_text: str, tab_id: str | None) -> List[Dict[str, Any]]:
    """
    Convertir Markdown simple a requests InsertText.
    Si se provee tab_id, cada request apunta a esa tab (cuando aplica).
    """
    lines = md_text.splitlines()
    requests: List[Dict[str, Any]] = []
    for line in lines:
        req: Dict[str, Any] = {
            "insertText": {
                "location": {"index": 1},
                "text": line + "\n",
            }
        }
        if tab_id:
            req["insertText"]["tabId"] = tab_id
        requests.append(req)
    return requests


# --- Tabs helpers (Docs) ---

def tab_start_marker(name: str) -> str:
    return f":::TAB {name} START:::"


def tab_end_marker(name: str) -> str:
    return f":::TAB {name} END:::"


def gdoc_build_tab_requests(tab_name: str, md_text: str, tab_id: str | None) -> List[Dict[str, Any]]:
    """Construye requests simples dirigidos a una tab específica si hay tab_id."""
    reqs: List[Dict[str, Any]] = []
    header = f"\n# {tab_name}\n\n"
    h_req: Dict[str, Any] = {"insertText": {"location": {"index": 1}, "text": header}}
    if tab_id:
        h_req["insertText"]["tabId"] = tab_id
    reqs.append(h_req)
    for line in md_text.splitlines():
        req: Dict[str, Any] = {"insertText": {"location": {"index": 1}, "text": line + "\n"}}
        if tab_id:
            req["insertText"]["tabId"] = tab_id
        reqs.append(req)
    return reqs

