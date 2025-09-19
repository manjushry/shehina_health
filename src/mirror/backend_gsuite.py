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
        raise NotImplementedError

    def gdoc_batch_update(self, document_id: str, requests: List[Dict[str, Any]]) -> None:
        raise NotImplementedError

    # Docs Tabs (modelo por secciones o named ranges)
    def gdoc_list_tabs(self, document_id: str) -> List[str]:
        """
        Retorna la lista de 'tabs' lógicos en el documento. Implementación sugerida:
        - Buscar encabezados H1/H2 y/o namedRanges que sigan convención TAB::<name>.
        - Alternativamente, detectar marcadores especiales de inicio/fin (ver gsuite_format).
        """
        raise NotImplementedError

    def gdoc_upsert_tab(self, document_id: str, tab_name: str, md_text: str) -> None:
        """
        Crea o actualiza el contenido de una 'tab' identificada por nombre.
        Estrategia:
        - Si existe named range para la tab, reemplazar su rango con requests MD→GDoc.
        - Si no existe, crear sección (encabezado/markers) y escribir contenido.
        """
        raise NotImplementedError

    def gdoc_extract_tab(self, document_id: str, tab_name: str) -> str:
        """Extrae el contenido de una 'tab' como Markdown (aproximado)."""
        raise NotImplementedError

