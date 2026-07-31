from datetime import datetime

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
        app_name=current_app.config["APP_NAME"],
        current_year=datetime.now().year,
    )
