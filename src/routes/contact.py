from datetime import datetime

from flask import Blueprint, current_app, render_template

bp = Blueprint("contact", __name__)


@bp.route("/")
def contact() -> str:
    """Render the application's "contact us" page.

    Returns:
        str: The rendered HTML for the contact information page.
    """
    return render_template(
        "contact.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now().year,
    )
