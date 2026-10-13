"""
pages.home - Landing page blueprint
-----------------------------------
"""

from datetime import UTC, datetime

from flask import Blueprint, current_app, render_template, send_from_directory
from werkzeug.wrappers import Response

bp = Blueprint("home", __name__)


@bp.get("/robots.txt")
def robots_txt() -> Response:
    """Serve the crawler policy at the site root."""
    static_folder = current_app.static_folder
    if static_folder is None:
        raise RuntimeError("The application static folder is not configured.")
    return send_from_directory(static_folder, "robots.txt", mimetype="text/plain")


@bp.route("/home")
@bp.route("/")
def home() -> str:
    """Render the application's landing page.

    Returns:
        str: The rendered HTML for the landing page.
    """
    return render_template(
        "home.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
    )
