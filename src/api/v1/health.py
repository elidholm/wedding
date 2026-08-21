"""
api.v1.health - Health check API resource
-----------------------------------------
"""

from flask import Blueprint

bp = Blueprint("health", __name__)


@bp.get("")
def health_check() -> tuple[dict[str, str], int]:
    return {"status": "healthy"}, 200
