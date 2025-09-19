from __future__ import annotations

from .gws_config import apply_gws_config


def link_gdrive(config: str | None = None):
    """Crea el enlace local a la carpeta de Google Drive según la config unificada.
    Config puede ser ruta a YML/JSON; si es None, se autodetecta.
    Devuelve un dict con resultado y mensajes.
    """
    return apply_gws_config(config)

__all__ = ["apply_gws_config", "link_gdrive"]
