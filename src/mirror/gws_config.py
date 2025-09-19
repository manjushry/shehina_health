from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Any, Dict, Optional, Tuple


def _simple_yaml_load(text: str) -> Dict[str, Any]:
    """Carga YAML muy simple (clave: valor) para configs triviales sin listas.
    Soporta strings entrecomillados y booleanos.
    """
    data: Dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        # quitar comentarios al final
        if " #" in val:
            val = val.split(" #", 1)[0].strip()
        if val.startswith(("'", '"')) and val.endswith(("'", '"')):
            val = val[1:-1]
        elif val.lower() in {"true", "false"}:
            val = val.lower() == "true"
        data[key] = val
    return data


def load_gws_config(explicit_path: Optional[str] = None) -> Tuple[Dict[str, Any], str]:
    """Carga configuración GWS desde un único lugar.
    Búsqueda en este orden:
      1) explicit_path si se pasa
      2) config/gws/config_google_workspace.yml
      3) config/gws/config_google_workspace.json
      4) config/gws/config.yml (legacy)
    Devuelve (config, path_or_hint).
    """
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    root = os.getcwd()
    candidates.append(os.path.join(root, "config", "gws", "config_google_workspace.yml"))
    candidates.append(os.path.join(root, "config", "gws", "config_google_workspace.json"))
    candidates.append(os.path.join(root, "config", "gws", "config.yml"))

    for path in candidates:
        if os.path.exists(path):
            try:
                if path.endswith(".json"):
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f), path
                # YAML muy simple
                with open(path, "r", encoding="utf-8") as f:
                    return _simple_yaml_load(f.read()), path
            except Exception as e:  # noqa: BLE001
                return {}, f"error reading {path}: {e}"
    return {}, "not-found"


def _ensure_gitignore(repo_root: str, entry: str) -> bool:
    gi = os.path.join(repo_root, ".gitignore")
    try:
        lines: list[str] = []
        if os.path.exists(gi):
            with open(gi, "r", encoding="utf-8") as f:
                lines = [ln.rstrip("\n") for ln in f.readlines()]
        if entry not in lines:
            lines.append(entry)
            with open(gi, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            return True
    except Exception:
        return False
    return False


def _create_windows_link(link_type: str, local_link_path: str, target_path: str) -> Tuple[bool, str]:
    # Usa mklink en CMD para crear junction o symlink
    if not os.path.exists(target_path):
        return False, f"target does not exist: {target_path}"
    # Crear directorio padre si hace falta
    parent = os.path.dirname(local_link_path)
    os.makedirs(parent, exist_ok=True)
    if os.path.exists(local_link_path):
        return True, "link already exists"

    if link_type.lower() == "junction":
        cmd = ["cmd", "/c", "mklink", "/J", local_link_path, target_path]
    elif link_type.lower() == "symlink":
        cmd = ["cmd", "/c", "mklink", "/D", local_link_path, target_path]
    else:
        return False, f"unsupported link_type: {link_type}"
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        ok = res.returncode == 0
        msg = res.stdout.strip() or res.stderr.strip()
        return ok, msg
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def apply_gws_config(explicit_path: Optional[str] = None) -> Dict[str, Any]:
    """Aplica la configuración GWS: crea link local a carpeta de Drive y asegura .gitignore.
    Retorna dict con resultados.
    """
    cfg, path_hint = load_gws_config(explicit_path)
    result: Dict[str, Any] = {"config_path": path_hint}
    if not cfg:
        result.update({"ok": False, "error": f"No config found ({path_hint})"})
        return result

    gdrive_documents_path = cfg.get("gdrive_documents_path")
    local_link_path = cfg.get("local_link_path")
    link_type = (cfg.get("link_type") or "junction")
    ensure_gitignore = bool(cfg.get("ensure_gitignore", True))

    if not (gdrive_documents_path and local_link_path):
        result.update({"ok": False, "error": "Missing gdrive_documents_path or local_link_path"})
        return result

    repo_root = os.getcwd()
    gi_updates: list[str] = []
    if ensure_gitignore:
        if _ensure_gitignore(repo_root, "documentos/"):
            gi_updates.append("documentos/")

    link_ok, link_msg = _create_windows_link(link_type, local_link_path, gdrive_documents_path)
    result.update({
        "ok": link_ok,
        "link_message": link_msg,
        "gitignore_added": gi_updates,
    })
    return result
