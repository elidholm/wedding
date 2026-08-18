from datetime import UTC, datetime

from flask import Blueprint, current_app, render_template

bp = Blueprint("home", __name__)


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
