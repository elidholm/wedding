"""
pages.seating - Seating page blueprint
--------------------------------------
"""

from datetime import UTC, datetime

from flask import Blueprint, current_app, render_template

bp = Blueprint("seating", __name__)


@bp.route("/")
@bp.route("")
def seating() -> str:
    """Render the application's "seating" page.

    Returns:
        str: The rendered HTML for the page containing table seating information.
    """
    return render_template(
        "seating.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
    )
