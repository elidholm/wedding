"""
api.v1.auth - Admin authentication API resource
-----------------------------------------------

This module defines JSON endpoints for admin login and logout. The
server-rendered admin pages call these endpoints instead of mutating the
Flask session directly.
"""

import hmac
import logging

from flask import Blueprint, Response, current_app, jsonify, request, session

from api.extensions import limiter

_log = logging.getLogger(__name__)


bp = Blueprint("auth", __name__)


def _json(code: str, message: str, status: int) -> Response:
    """Build a JSON response for an auth outcome."""
    response = jsonify({"code": code, "message": message})
    response.status_code = status
    return response


@bp.post("/login")
@limiter.limit("5 per minute")
def login() -> Response:
    """Authenticate an admin using a JSON password payload."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        _log.error("Invalid login request: not a JSON object.")
        return _json("invalid_request", "Request body must be a valid JSON object.", 400)

    password = payload.get("password")
    if not isinstance(password, str) or not password:
        _log.error("Invalid login request: missing or empty password.")
        return _json("invalid_request", "Password is required.", 400)

    config = current_app.config["CONFIG"]
    if not config.admin_password:
        _log.error("Admin login attempted but no password is configured.")
        return _json("admin_login_disabled", "Admin login is not configured.", 503)

    if not hmac.compare_digest(password.encode(), config.admin_password.encode()):
        _log.warning("Admin login failed: incorrect password.")
        session.pop("is_admin", None)
        return _json("invalid_credentials", "Incorrect password.", 401)

    _log.info("Admin login successful.")
    session["is_admin"] = True
    return _json("login_successful", "Logged in successfully.", 200)


@bp.post("/logout")
@limiter.limit("10 per minute")
def logout() -> Response:
    """Log out the current admin session."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        _log.error("Invalid logout request: not a JSON object.")
        return _json("invalid_request", "Request body must be a valid JSON object.", 400)

    _log.info("Admin logout successful.")
    session.pop("is_admin", None)
    return _json("logout_successful", "Logged out successfully.", 200)
