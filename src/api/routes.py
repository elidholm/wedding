"""
api.routes - Aggregates and registers all API version blueprints
----------------------------------------------------------------

This module is the single entry point ``main.py`` imports for the entire API
layer. It delegates to each API version's own ``routes.register`` function,
so ``main.py`` never needs to know which versions exist or what prefix they
use. Adding a new API version (e.g. ``v2``) only requires wiring it up here.
"""

from flask import Flask

from api.v1.routes import register as register_v1


def register(app: Flask) -> None:
    """Register all API version blueprints on the given Flask app.

    Args:
        app (Flask): The Flask application to register the API blueprints on.
    """
    register_v1(app)
