"""
api.v1.health - Health check API resource
-----------------------------------------
"""

from flask import Blueprint, Response, jsonify

from api.extensions import limiter

bp = Blueprint("health", __name__)


@bp.get("")
@limiter.limit("10 per minute")
def health_check() -> Response:
    response = jsonify({"status": "healthy"})
    response.status_code = 200
    return response
