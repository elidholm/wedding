"""
pages.rsvp - Page where guests can RSVP to the wedding.
-------------------------------------------------------
"""

import secrets
from datetime import UTC, datetime

from flask import Blueprint, current_app, make_response, redirect, render_template, request, session, url_for
from werkzeug.wrappers import Response

from services.rsvp_service import find_guest, save_rsvp

bp = Blueprint("rsvp", __name__)


def _get_or_create_csrf_token() -> str:
    """Return this session's CSRF token for the RSVP form, generating one if missing.

    Returns:
        str: The session's synchronizer-pattern CSRF token.
    """
    token = session.get("rsvp_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["rsvp_csrf_token"] = token
    return token


@bp.route("/", methods=["GET", "POST"])
@bp.route("", methods=["GET", "POST"])
def rsvp() -> str | Response:
    """Render the RSVP search page, or handle its guest-lookup form submission.

    On `POST`, validates the submitted `guest_id` is a six-digit number
    belonging to a known guest, establishes an authenticated guest session
    for that guest_id, and redirects to their RSVP page. Otherwise, re-renders
    this search page with an inline error.

    Returns:
        str | Response: The rendered HTML for the RSVP search page, or a
        redirect response to the guest's RSVP page.
    """
    error = None
    guest_id = request.form.get("guest_id", "")
    if request.method == "POST":
        if not guest_id.isdigit() or len(guest_id) != 6:
            error = "Ange det sexsiffriga ID-numret från din inbjudan."
        elif find_guest(guest_id) is None:
            error = "Vi hittar ingen inbjudan med det ID-numret. Kontrollera numret och försök igen."
        else:
            session["rsvp_guest_id"] = guest_id
            return redirect(url_for("rsvp.rsvp_guest", guest_id=guest_id))

    return render_template(
        "rsvp.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
        error=error,
        guest_id=guest_id,
    )


@bp.route("/<int:guest_id>", methods=["GET", "POST"])
def rsvp_guest(guest_id: int) -> str | Response:
    """Render the RSVP page for a specific guest.

    Access requires an authenticated guest session (established by a
    successful lookup on the search page) matching this guest_id; the
    six-digit guest_id in the URL is not accepted as sole proof of identity,
    since it is guessable. POSTs are additionally checked against a
    per-session CSRF token embedded in the form.

    Args:
        guest_id (int): The unique identifier for the guest.

    Returns:
        str | Response: The rendered HTML for the RSVP page for the specific
        guest, or a redirect back to the search page if not authenticated.
    """
    guest_id_str = str(guest_id).zfill(6)
    if session.get("rsvp_guest_id") != guest_id_str:
        return redirect(url_for("rsvp.rsvp"))

    guest = find_guest(guest_id_str)
    if guest is None:
        session.pop("rsvp_guest_id", None)
        response = make_response(
            render_template(
                "rsvp_guest.html",
                config=current_app.config["CONFIG"],
                current_year=datetime.now(tz=UTC).year,
                guest_id=guest_id_str,
                guest=None,
                error="Vi hittar ingen inbjudan med det ID-numret. Kontrollera numret och försök igen.",
            ),
            404,
        )
        return response

    error = None
    saved = False
    if request.method == "POST":
        submitted_csrf_token = request.form.get("csrf_token", "")
        if not secrets.compare_digest(submitted_csrf_token, session.get("rsvp_csrf_token", "")):
            error = "Sessionen har gått ut. Ladda om sidan och försök igen."
        else:
            try:
                guest = save_rsvp(guest_id_str, request.form)
                saved = True
            except ValueError as exc:
                error = str(exc)

    return render_template(
        "rsvp_guest.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
        guest_id=guest_id_str,
        guest=guest,
        saved=saved,
        error=error,
        csrf_token=_get_or_create_csrf_token(),
    )
