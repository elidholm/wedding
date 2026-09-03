"""
api.routes - Aggregates and registers all API version blueprints
----------------------------------------------------------------

This module is the single entry point ``main.py`` imports for the entire API
layer. It delegates to each API version's own ``routes.register`` function,
so ``main.py`` never needs to know which versions exist or what prefix they
use. Adding a new API version (e.g. ``v2``) only requires wiring it up here.

Attributes:
    API_PATH_PREFIX (str): The URL prefix for all API routes.
"""

from typing import cast

from flask import Flask, Response, jsonify, request
from werkzeug.exceptions import HTTPException

from api.extensions import limiter
from api.v1.routes import register as register_v1

API_PATH_PREFIX = "/api"


def register(app: Flask) -> None:
    """Register all API version blueprints on the given Flask app.

    Also registers an app-level 405 handler so that hitting an API endpoint
    with an unsupported HTTP method returns a JSON error, rather than
    Flask's default HTML error page.

    Args:
        app (Flask): The Flask application to register the API blueprints on.
    """
    limiter.init_app(app)
    register_v1(app, api_prefix=API_PATH_PREFIX)

    @app.errorhandler(405)
    def _handle_api_method_not_allowed(exc: HTTPException) -> Response:
        """Return a JSON 405 error for API requests, leaving other routes untouched."""
        if request.path.startswith(API_PATH_PREFIX + "/"):
            response = jsonify({"error": "Method not allowed."})
            response.status_code = 405
            return response

        return cast(Response, Response.force_type(exc.get_response(), request.environ))
