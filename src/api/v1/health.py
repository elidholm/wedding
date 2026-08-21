"""
api.v1.health - Health check API resource
-----------------------------------------
"""

from flask import Blueprint, Response, jsonify

bp = Blueprint("health", __name__)


@bp.get("")
def health_check() -> Response:
    response = jsonify({"status": "healthy"})
    response.status_code = 200
    return response
