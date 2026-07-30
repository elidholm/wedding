"""The `rsvp` blueprint: page where guests can RSVP to the wedding."""

from flask import Blueprint, current_app, render_template

bp = Blueprint("rsvp", __name__)


@bp.route("/")
def rsvp() -> str:
    """Render the application's landing page."""
    return render_template("rsvp.html", app_name=current_app.config["APP_NAME"])
