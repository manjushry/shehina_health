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
    """Esqueleto: convertir Markdown a requests de GDoc (simplificado)."""
    # En siguientes épicas, usar un parser MD y mapear a requests (párrafos, headers, listas).
    lines = md_text.splitlines()
    requests: List[Dict[str, Any]] = []
    for line in lines:
        requests.append({
            "insertText": {"location": {"index": 1}, "text": line + "\n"}
        })
    return requests

