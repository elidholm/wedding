"""
pages.rsvp - Page where guests can RSVP to the wedding.
-------------------------------------------------------

Every invite has a personal link, ``/rsvp/<invite UUID>``, printed as a QR
code on the invitation. Opening it shows one RSVP form covering every guest
on the invite. Guests without the link can paste the invite code (or the
whole link) into the form on ``/rsvp``.
"""

import logging
import secrets
from datetime import UTC, datetime
from uuid import UUID

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.wrappers import Response

from api.extensions import limiter
from db.schemas import Invite
from db.session import get_db_session
from services.rsvp_service import RsvpService

_log = logging.getLogger(__name__)

bp = Blueprint("rsvp", __name__)

_SESSION_INVITE_KEY = "rsvp_invite_id"
_SESSION_CSRF_KEY = "rsvp_csrf_token"
_NOT_FOUND_ERROR = "Vi hittar ingen inbjudan med den koden. Kontrollera koden och försök igen."


def _get_or_create_csrf_token() -> str:
    """Return this session's CSRF token for the RSVP form, generating one if missing.

    Returns:
        str: The session's synchronizer-pattern CSRF token.
    """
    token = session.get(_SESSION_CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[_SESSION_CSRF_KEY] = token
    return token


def _parse_invite_code(code: str) -> str | None:
    """Parse a pasted invite code, or a whole RSVP link, into a canonical invite UUID.

    Args:
        code (str): The code (or link) entered by the guest.

    Returns:
        str | None: The canonical lowercase UUID string, or None if the code
        doesn't contain a valid UUID.
    """
    candidate = code.strip().rstrip("/").rsplit("/", 1)[-1]
    try:
        return str(UUID(candidate))
    except ValueError:
        return None


def _render_rsvp_invite(invite: Invite | None, status: int = 200, **context: object) -> tuple[str, int]:
    """Render an invite's RSVP page.

    Args:
        invite (Invite | None): The invite to render, or None for a not-found page.
        status (int): The HTTP status code to respond with. Defaults to 200.
        **context (object): Extra template context (e.g. ``error``, ``saved``).

    Returns:
        tuple[str, int]: The rendered HTML and its status code.
    """
    html = render_template(
        "rsvp_invite.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
        invite=invite,
        **context,
    )
    return html, status


@bp.route("/", methods=["GET", "POST"])
@bp.route("", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def rsvp() -> str | Response:
    """Render the RSVP lookup page, or handle its invite-code form submission.

    On `POST`, validates that the submitted `invite_id` (an invite UUID, or
    a whole RSVP link containing one) belongs to a known invite and
    redirects to that invite's RSVP page. Otherwise, re-renders this page
    with an inline error.

    Returns:
        str | Response: The rendered HTML for the RSVP lookup page, or a
        redirect response to the invite's RSVP page.
    """
    error = None
    invite_code = request.form.get("invite_id", "")
    if request.method == "POST":
        invite_id = _parse_invite_code(invite_code)
        if invite_id is None:
            error = "Ange koden från din inbjudan, eller klistra in hela länken."
        elif RsvpService(get_db_session()).get_invite(invite_id) is None:
            error = _NOT_FOUND_ERROR
        else:
            return redirect(url_for("rsvp.rsvp_invite", invite_id=invite_id))

    return render_template(
        "rsvp.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
        error=error,
        invite_id=invite_code,
    )


@bp.route("/<uuid:invite_id>", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def rsvp_invite(invite_id: UUID) -> tuple[str, int] | Response:
    """Render, or save, the RSVP form for every guest on an invite.

    The invite's unguessable UUID link is the guest's credential: a `GET`
    of a known invite marks this session as authenticated for it. A `POST`
    is only accepted from a session authenticated for this same invite, and
    must carry the session's CSRF token.

    Args:
        invite_id (UUID): The invite's UUID.

    Returns:
        tuple[str, int] | Response: The rendered RSVP page and its status
        code (404 for an unknown invite), or a redirect back to this page
        for a `POST` from an unauthenticated session.
    """
    invite_id_str = str(invite_id)
    service = RsvpService(get_db_session())
    invite = service.get_invite(invite_id_str)
    if invite is None:
        if session.get(_SESSION_INVITE_KEY) == invite_id_str:
            session.pop(_SESSION_INVITE_KEY)
        return _render_rsvp_invite(None, 404, error=_NOT_FOUND_ERROR)

    if request.method == "GET":
        session[_SESSION_INVITE_KEY] = invite_id_str
        return _render_rsvp_invite(invite, csrf_token=_get_or_create_csrf_token())

    if session.get(_SESSION_INVITE_KEY) != invite_id_str:
        return redirect(url_for("rsvp.rsvp_invite", invite_id=invite_id_str))

    error = None
    saved = False
    status = 200
    # Compare bytes: compare_digest raises TypeError on non-ASCII str input.
    submitted_csrf_token = request.form.get("csrf_token", "").encode()
    expected_csrf_token = str(session.get(_SESSION_CSRF_KEY, "")).encode()
    if not secrets.compare_digest(submitted_csrf_token, expected_csrf_token):
        error = "Sessionen har gått ut. Ladda om sidan och försök igen."
    elif invite.guests:
        try:
            service.save_rsvp(invite_id_str, request.form)
            saved = True
        except ValueError as exc:
            error = str(exc)
        except SQLAlchemyError:
            _log.exception("Failed to save RSVP for invite %s.", invite_id_str)
            error = "Något gick fel när svaret skulle sparas. Försök igen om en stund."
            status = 500

    return _render_rsvp_invite(invite, status, saved=saved, error=error, csrf_token=_get_or_create_csrf_token())
