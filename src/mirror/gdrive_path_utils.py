from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, Iterable, List, Optional


_DOC_URL_RE = re.compile(r"/d/([a-zA-Z0-9_-]{10,})/")


def extract_id_from_gdoc_file(path: str) -> Optional[str]:
    """Lee un archivo .gdoc/.gsheet/.gslides (JSON) y retorna el ID.
    Fallback: parsea la URL si no hay doc_id.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        doc_id = data.get("doc_id") or data.get("id")
        if doc_id:
            return doc_id
        url = data.get("url") or ""
        m = _DOC_URL_RE.search(url)
        return m.group(1) if m else None
    except Exception:
        return None


def extract_folder_id_from_shortcut_path(path: str) -> Optional[str]:
    """Extrae el folderId de una ruta local que contiene .shortcut-targets-by-id.
    Ej: G:\\.shortcut-targets-by-id\\<folderId>\\...
    """
    norm = path.replace("/", "\\")
    token = ".shortcut-targets-by-id\\"
    idx = norm.find(token)
    if idx == -1:
        return None
    rest = norm[idx + len(token) :]
    parts = rest.split("\\")
    return parts[0] if parts else None


def resolve_drive_path_to_id(drive: Any, root_folder_id: str, path_segments: Iterable[str]) -> Optional[str]:
    """Resuelve una ruta (segmentos) bajo un folderId de Drive usando Drive API v3.
    - drive: cliente googleapiclient.discovery.build('drive','v3')
    - root_folder_id: folderId base
    - path_segments: [subcarpeta, ..., filename]
    Devuelve el fileId o None si no se encuentra.
    """
    parent = root_folder_id
    parts = list(path_segments)
    # carpetas intermedias
    for seg in parts[:-1]:
        seg_escaped = seg.replace("'", "\\'")
        q = f"name='{seg_escaped}' and '{parent}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        resp = drive.files().list(q=q, fields="files(id,name)", pageSize=10).execute()
        files = resp.get("files", [])
        if not files:
            return None
        # Si hay duplicados, tomar el primero determinísticamente
        parent = files[0]["id"]

    # archivo final (puede ser carpeta si así se desea)
    leaf = parts[-1] if parts else None
    if leaf is None:
        return parent
    leaf_escaped = leaf.replace("'", "\\'")
    q = f"name='{leaf_escaped}' and '{parent}' in parents and trashed=false"
    resp = drive.files().list(q=q, fields="files(id,name,mimeType)", pageSize=10).execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None
