"""Pytest configuration shared by all tests.

The modules under ``app/`` use flat imports (e.g. ``from config import
AppConfig`` rather than ``from app.config import AppConfig``), which only
resolve correctly when ``app/`` itself — not the repo root — is on
``sys.path``. This mirrors how the app is actually run (``uv run python
app/main.py``), so tests need the same setup to import those modules.
"""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))
