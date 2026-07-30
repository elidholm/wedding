"""Pytest configuration shared by all tests.

The modules under ``src/`` use flat imports (e.g. ``from config import
AppConfig`` rather than ``from src.config import AppConfig``), which only
resolve correctly when ``src/`` itself — not the repo root — is on
``sys.path``. This mirrors how the app is actually run (``uv run python
src/main.py``), so tests need the same setup to import those modules.
"""

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
