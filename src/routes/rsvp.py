"""The `rsvp` blueprint: page where guests can RSVP to the wedding."""

from datetime import UTC, datetime

from flask import Blueprint, current_app, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

bp = Blueprint("rsvp", __name__)


@bp.route("/", methods=["GET", "POST"])
@bp.route("")
def rsvp() -> str | Response:
    """Render the RSVP search page, or handle its guest-lookup form submission.

    On `POST`, reads `guest_id` from the submitted form and redirects to the
    matching guest's RSVP page. If `guest_id` is missing or not a valid
    integer, redirects back to this same search page instead of erroring.

    Returns:
        str | Response: The rendered HTML for the RSVP search page, or a
        redirect response to the guest's RSVP page.
    """
    if request.method == "POST":
        try:
            guest_id = int(request.form["guest_id"])
        except (KeyError, ValueError):
            return redirect(url_for("rsvp.rsvp"))
        return redirect(url_for("rsvp.rsvp_guest", guest_id=guest_id))

    return render_template(
        "rsvp.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
    )


@bp.route("/<int:guest_id>")
def rsvp_guest(guest_id: int) -> str:
    """Render the RSVP page for a specific guest.

    Args:
        guest_id (int): The unique identifier for the guest.

    Returns:
        str: The rendered HTML for the RSVP page for the specific guest.
    """
    return render_template(
        "rsvp_guest.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
        guest_id=guest_id,
    )
