from __future__ import annotations

"""
BackendGSuite: Acceso unificado a Google Drive, Sheets y Docs.

Concepto:
- Capa delgada que encapsula clientes oficiales (google-api-python-client) o wrappers
  equivalentes. Mantener interfaces simples, testeables y con mínima superficie.

Nota: Este esqueleto evita dependencias fuertes inmediatas. Implementación completa en
épicas siguientes.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import json
import os


@dataclass
class GSuiteConfig:
    workspace_email: Optional[str] = None
    impersonate_user: Optional[str] = None
    project_id: Optional[str] = None
    # Otros campos relevantes (scopes, etc.)


class BackendGSuite:
    def __init__(self, credentials_path: str, config: Optional[GSuiteConfig] = None) -> None:
        self.credentials_path = credentials_path
        self.config = config or GSuiteConfig()
        # TODO: inicializar clientes de Drive/Sheets/Docs cuando se integren dependencias

    # Drive
    def drive_list(self, query: str) -> List[Dict[str, Any]]:
        """Lista archivos por query (mimicking Drive v3 files.list q)."""
        raise NotImplementedError

    def drive_get_file(self, file_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def drive_download(self, file_id: str, mime_type: Optional[str] = None) -> bytes:
        raise NotImplementedError

    def drive_upload(self, name: str, data: bytes, mime_type: str, folder_id: Optional[str] = None) -> str:
        raise NotImplementedError

    # Sheets
    def sheets_read_range(self, spreadsheet_id: str, a1_range: str) -> List[List[Any]]:
        raise NotImplementedError

    def sheets_write_range(self, spreadsheet_id: str, a1_range: str, values: List[List[Any]]) -> None:
        raise NotImplementedError

    def sheets_add_sheet(self, spreadsheet_id: str, title: str) -> int:
        """Crea una pestaña y retorna sheetId."""
        raise NotImplementedError

    # Docs
    def gdoc_read(self, document_id: str) -> Dict[str, Any]:
        """
        Implementación mínima de prueba: si existe un mock JSON en disco,
        lo cargamos; de lo contrario, NotImplementedError. Sirve para tests offline.
        Convención: config/gws/google_workspace.json con {"documents": {"<id>": "path.json"}}
        """
        cfg_path = os.path.join(os.getcwd(), "config", "gws", "google_workspace.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                mapping = (cfg.get("documents") or {})
                mock_path = mapping.get(document_id)
                if mock_path and os.path.exists(mock_path):
                    with open(mock_path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:  # noqa: BLE001
                pass
        raise NotImplementedError("gdoc_read real pendiente de integrar Google API; use mock en config/google_workspace.json")

    def gdoc_batch_update(self, document_id: str, requests: List[Dict[str, Any]]) -> None:
        # Stub para pruebas: no-op si se usa modo mock.
        return None

    # Docs Tabs (modelo por secciones o named ranges)
    def gdoc_list_tabs(self, document_id: str) -> List[str]:
        """
        Retorna la lista de 'tabs' lógicos en el documento. Implementación sugerida:
        - Buscar encabezados H1/H2 y/o namedRanges que sigan convención TAB::<name>.
        - Alternativamente, detectar marcadores especiales de inicio/fin (ver gsuite_format).
        """
        doc = self.gdoc_read(document_id)
        out: List[str] = []
        def walk(ts: List[Dict[str, Any]]):
            for t in ts:
                props = (t.get("tabProperties") or {})
                title = props.get("title")
                if title:
                    out.append(title)
                walk(t.get("childTabs") or [])
        walk(doc.get("tabs") or [])
        return out

    def gdoc_upsert_tab(self, document_id: str, tab_name: str, md_text: str) -> None:
        """
        Crea o actualiza el contenido de una 'tab' identificada por nombre.
        Estrategia:
        - Si existe named range para la tab, reemplazar su rango con requests MD→GDoc.
        - Si no existe, crear sección (encabezado/markers) y escribir contenido.
        """
    # Este backend delegará en front para construir requests; aquí sólo sería IO real.
    raise NotImplementedError("Use alchemist.gdoc_front.upsert_tab_from_md para construir requests; backend ejecuta batch_update real")

    def gdoc_extract_tab(self, document_id: str, tab_name: str) -> str:
        """Extrae el contenido de una 'tab' como Markdown (aproximado)."""
        raise NotImplementedError

