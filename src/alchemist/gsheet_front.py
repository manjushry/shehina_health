from __future__ import annotations

"""Frontend de Alchemist para Google Sheets."""

from typing import Any, List, Tuple

from mirror.backend_gsuite import BackendGSuite
from mirror.gsuite_format import table_to_gsheet, gsheet_to_table


def write_table(backend: BackendGSuite, spreadsheet_id: str, a1_range: str, table: List[List[Any]]) -> None:
    values = table_to_gsheet(table)
    backend.sheets_write_range(spreadsheet_id, a1_range, values)


def read_table(backend: BackendGSuite, spreadsheet_id: str, a1_range: str) -> List[List[Any]]:
    values = backend.sheets_read_range(spreadsheet_id, a1_range)
    return gsheet_to_table(values)


def ensure_sheet(backend: BackendGSuite, spreadsheet_id: str, title: str) -> int:
    return backend.sheets_add_sheet(spreadsheet_id, title)
