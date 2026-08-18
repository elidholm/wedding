from datetime import UTC, datetime

from flask import Blueprint, current_app, render_template

bp = Blueprint("itinerary", __name__)


@bp.route("/")
@bp.route("")
def itinerary() -> str:
    """Render the application's "itinerary" page.

    Returns:
        str: The rendered HTML for the itinerary page.
    """
    return render_template(
        "itinerary.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
    )
