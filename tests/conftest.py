"""Pytest configuration shared by all tests.

The modules under ``src/`` use flat imports (e.g. ``from core.config import
Config`` rather than ``from src.core.config import Config``), which only
resolve correctly when ``src/`` itself — not the repo root — is on
``sys.path``. This mirrors how the app is actually run (``uv run python
src/main.py``), so tests need the same setup to import those modules.
"""

import os
import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Force every test run to use an in-memory SQLite database instead of the real
# dev database file. This must be set before anything imports `db.schemas`
# (which reads `core.config.get_config()` — a cached singleton — at import
# time), so it's set here, in the first module pytest loads.
os.environ.setdefault("DB_URL", "sqlite:///:memory:")
