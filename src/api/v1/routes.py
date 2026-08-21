"""
api.v1.routes - Aggregates and registers all v1 API resource blueprints
-----------------------------------------------------------------------

This module wires up every v1 API resource blueprint (e.g. ``health``) to a
Flask application under the ``/api/v1`` namespace.

Attributes:
    URL_PREFIX (str): The URL prefix for all v1 API routes.
"""

from flask import Flask

from api.v1.guests import bp as guests_bp
from api.v1.health import bp as health_bp

URL_PREFIX = "/api/v1"


def register(app: Flask) -> None:
    """Register all v1 API resource blueprints on the given Flask app.

    Args:
        app (Flask): The Flask application to register the v1 resource
            blueprints on.
    """
    app.register_blueprint(health_bp, url_prefix=f"{URL_PREFIX}/health")
    app.register_blueprint(guests_bp, url_prefix=f"{URL_PREFIX}/guests")
