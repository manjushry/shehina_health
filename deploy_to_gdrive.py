#!/usr/bin/env python3
"""
Script CLI para desplegar estructura local a Google Drive usando APIs.
Punto de entrada principal que invoca src/mirror/drive_deployer.py
"""
import sys
from pathlib import Path

# Agregar src al path para imports
repo_root = Path(__file__).parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

from mirror.drive_deployer import main

if __name__ == "__main__":
    sys.exit(main())