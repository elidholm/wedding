"""
api.v1.routes - Aggregates and registers all v1 API resource blueprints
-----------------------------------------------------------------------

This module wires up every v1 API resource blueprint (e.g. ``health``) to a
Flask application under the appropriate namespace.

Attributes:
    VERSION (str): The API version string, used in the URL prefix for all
        v1 routes.
"""

from flask import Flask

from api.v1.guests import bp as guests_bp
from api.v1.health import bp as health_bp

VERSION = "v1"


def register(app: Flask, api_prefix: str) -> None:
    """Register all v1 API resource blueprints on the given Flask app.

    Args:
        app (Flask): The Flask application to register the v1 resource
            blueprints on.
        api_prefix (str): The URL prefix for all API routes (e.g. ``/api``).
    """
    app.register_blueprint(health_bp, url_prefix=f"{api_prefix}/{VERSION}/health")
    app.register_blueprint(guests_bp, url_prefix=f"{api_prefix}/{VERSION}/guests")
