from flask import Blueprint

bp = Blueprint("health", __name__)


@bp.route("/")
@bp.route("")
def health_check() -> tuple[dict[str, str], int]:
    """Basic health check endpoint for the application.

    Returns:
        tuple[dict[str, str], int]: A tuple containing a dictionary with
        the health status and an HTTP status code.
    """
    return {"status": "healthy"}, 200
