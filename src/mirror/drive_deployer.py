from __future__ import annotations

import argparse
import datetime as dt
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from .gws_config import apply_gws_config, load_gws_config
from .gdrive_path_utils import extract_folder_id_from_shortcut_path


def _now_tag() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _is_empty_dir(p: Path) -> bool:
    return p.exists() and p.is_dir() and not any(p.iterdir())


def _backup_existing_local(local_link_path: Path) -> Optional[Path]:
    """Si existe una carpeta real en local_link_path, la mueve a un backup.
    Devuelve la ruta del backup o None si no se movió nada.
    Nota: No intenta detectar si es junction/symlink; si es reparse point, lo deja.
    """
    try:
        if not local_link_path.exists():
            return None
        # Heurística: si es un directorio y contiene archivos, asumir que es real
        if local_link_path.is_dir():
            # Si está vacío, permitir que se reemplace por el junction sin backup
            if _is_empty_dir(local_link_path):
                return None
            backup = local_link_path.parent / f"{local_link_path.name}.local_backup_{_now_tag()}"
            os.rename(str(local_link_path), str(backup))
            return backup
    except Exception:
        # Si no se puede mover, continuar sin bloquear
        return None
    return None


def _walk_local_tree(root: Path) -> Iterable[Path]:
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            yield Path(dirpath) / fn


def _google_clients_from_env(scopes: List[str]):
    """Construye clientes de Google Drive y Docs usando GOOGLE_APPLICATION_CREDENTIALS.
    Requiere permisos adecuados a la carpeta destino (My Drive / Shared Drive + domain delegation si aplica).
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not cred_path or not os.path.exists(cred_path):
        raise RuntimeError(f"Variable GOOGLE_APPLICATION_CREDENTIALS no configurada o archivo no existe: {cred_path}")
    
    creds = service_account.Credentials.from_service_account_file(cred_path, scopes=scopes)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    docs = None  # Por ahora no usamos Docs API
    return drive, docs


def _drive_find_single(drive, parent_id: str, name: str, mime_type: Optional[str] = None) -> Optional[Dict]:
    name_escaped = name.replace("'", "\\'")
    q = [f"name='{name_escaped}'", f"'{parent_id}' in parents", "trashed=false"]
    if mime_type:
        q.append(f"mimeType='{mime_type}'")
    resp = drive.files().list(q=" and ".join(q), fields="files(id,name,mimeType)", pageSize=10).execute()
    files = resp.get("files", [])
    return files[0] if files else None


def _drive_ensure_folder(drive, parent_id: str, name: str) -> str:
    folder_mt = "application/vnd.google-apps.folder"
    found = _drive_find_single(drive, parent_id, name, folder_mt)
    if found:
        return found["id"]
    body = {"name": name, "mimeType": folder_mt, "parents": [parent_id]}
    created = drive.files().create(body=body, fields="id").execute()
    return created["id"]


def _docs_create_with_text(docs, title: str, text: str) -> str:
    # Crea doc vacío
    d = docs.documents().create(body={"title": title}).execute()
    doc_id = d["documentId"]
    # Reemplaza contenido
    requests = [
        {"deleteContentRange": {"range": {"startIndex": 1, "endIndex": 1_000_000_000}}},
        {"insertText": {"location": {"index": 1}, "text": text}},
    ]
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    return doc_id


def _drive_upload_binary(drive, parent_id: str, local_path: Path) -> str:
    from googleapiclient.http import MediaFileUpload
    mime, _ = mimetypes.guess_type(str(local_path))
    media = MediaFileUpload(str(local_path), mimetype=mime or "application/octet-stream", resumable=False)
    body = {"name": local_path.name, "parents": [parent_id]}
    created = drive.files().create(body=body, media_body=media, fields="id").execute()
    return created["id"]


def deploy_local_to_drive(local_root: Path, drive_root_folder_id: str, dry_run: bool = True) -> Dict[str, List[str]]:
    """Recrea la estructura de local_root dentro de drive_root_folder_id.
    - Crea carpetas equivalentes
    - Convierte .md a archivos de texto (por compatibilidad API)
    - Sube otros archivos binarios tal cual
    """
    if not dry_run:
        scopes = [
            "https://www.googleapis.com/auth/drive",
            # "https://www.googleapis.com/auth/documents",  # Comentado por ahora
        ]
        drive, docs = _google_clients_from_env(scopes)

    # Map de carpetas creadas por ruta relativa
    folder_cache: Dict[str, str] = {"": drive_root_folder_id}
    created: List[str] = []
    skipped: List[str] = []

    def ensure_folder_path(rel_dir: Path) -> str:
        parts = [p for p in rel_dir.parts if p]
        parent = drive_root_folder_id
        current_rel = []
        for seg in parts:
            current_rel.append(seg)
            key = "/".join(current_rel)
            if key in folder_cache:
                parent = folder_cache[key]
                continue
            if not dry_run:
                parent = _drive_ensure_folder(drive, parent, seg)
            else:
                parent = f"FOLDER_{len(current_rel)}"  # Mock ID for dry-run
            folder_cache[key] = parent
        return parent

    for file_path in _walk_local_tree(local_root):
        rel = file_path.relative_to(local_root)
        parent_id = ensure_folder_path(rel.parent)
        
        if file_path.suffix.lower() == ".md":
            # Subir como archivo de texto por ahora (hasta habilitar Docs API)
            if dry_run:
                created.append(f"MD_FILE {rel}")
            else:
                fid = _drive_upload_binary(drive, parent_id, file_path)
                created.append(f"MD_FILE {rel} -> {fid}")
        else:
            if dry_run:
                created.append(f"FILE {rel}")
            else:
                fid = _drive_upload_binary(drive, parent_id, file_path)
                created.append(f"FILE {rel} -> {fid}")

    return {"created": created, "skipped": skipped}


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Despliega una estructura local a Google Drive usando APIs")
    p.add_argument("--config", help="Ruta a config GWS (yml/json). Autodetecta por defecto", default=None)
    p.add_argument("--source", help="Ruta local a desplegar; por defecto usa el backup del local_link si existe", default=None)
    p.add_argument("--dry-run", help="No aplica cambios; solo muestra plan", action="store_true")
    p.add_argument("--apply", help="Aplica cambios reales", action="store_true")
    args = p.parse_args(argv)

    if not args.dry_run and not args.apply:
        print("[INFO] No se indicó --dry-run ni --apply; ejecutando en modo --dry-run por seguridad.")
        args.dry_run = True

    cfg, cfg_path = load_gws_config(args.config)
    if not cfg:
        print(f"[ERROR] No se pudo cargar config GWS ({cfg_path})")
        return 2

    gdrive_documents_path = cfg.get("gdrive_documents_path")
    local_link_path = Path(cfg.get("local_link_path"))
    if not gdrive_documents_path or not local_link_path:
        print("[ERROR] Config incompleta: gdrive_documents_path o local_link_path")
        return 2

    # Asegurar junction: si existe carpeta local real, hacer backup y crear link
    backup_path = None
    if local_link_path.exists():
        backup_path = _backup_existing_local(local_link_path)

    res_link = apply_gws_config(args.config)
    print(f"[LINK] {res_link}")

    # Resolver folderId raíz desde la ruta .shortcut-targets-by-id
    root_folder_id = extract_folder_id_from_shortcut_path(gdrive_documents_path)
    if not root_folder_id:
        print(f"[ERROR] No se pudo extraer folderId desde gdrive_documents_path: {gdrive_documents_path}")
        return 2

    # Elegir fuente: --source o backup si existe
    source_dir = Path(args.source) if args.source else backup_path
    if not source_dir or not source_dir.exists():
        print("[ERROR] No se encontró carpeta fuente para desplegar. Use --source o asegúrese de tener backup.")
        return 2

    plan = deploy_local_to_drive(source_dir, root_folder_id, dry_run=args.dry_run and not args.apply)
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
