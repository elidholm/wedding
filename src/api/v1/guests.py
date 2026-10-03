"""
api.v1.guests - Guest API resource
----------------------------------

This module defines the API resource for managing guest records. It
provides endpoints for listing, creating, retrieving, updating, and
deleting guests.

Guest records are personal data (names, emails, allergies, food
preferences), so *every* endpoint in this resource requires an
authenticated admin session - the same ``is_admin`` session flag set by
``api.v1.auth``. Unauthenticated requests are rejected with a 401 before
the view ever runs.

Every response - success or error - is JSON, including validation
failures (400), not-found (404), and method-not-allowed (405) errors, so
API consumers never have to deal with Flask's default HTML error pages.
"""

import logging

from flask import Blueprint, Response, g, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.extensions import limiter
from api.v1.utils import error, json, parse_body
from db.schemas import SessionLocal
from models.guest import GuestCreate, GuestRead, GuestUpdate
from services.guest_service import GuestService

_log = logging.getLogger(__name__)

bp = Blueprint("guests", __name__)


def _get_db_session() -> Session:
    """Get (or lazily open) the current request's SQLAlchemy session.

    The session is stashed on Flask's request-scoped ``g`` object so every
    call within the same request reuses it, and is closed automatically by
    ``_close_db_session`` once the request tears down.

    Returns:
        Session: The current request's SQLAlchemy session.
    """
    if "guests_db_session" not in g:
        g.guests_db_session = SessionLocal()
    return g.guests_db_session


@bp.teardown_request
def _close_db_session(exception: BaseException | None = None) -> None:
    """Close this request's database session, rolling back first on error.

    Args:
        exception (BaseException | None): The exception that ended the
            request, if any, as passed by Flask's ``teardown_request`` hook.
    """
    session = g.pop("guests_db_session", None)
    if session is not None:
        if exception is not None:
            session.rollback()
        session.close()


def get_guest_service() -> GuestService:
    """Get a GuestService bound to the current request's database session.

    Returns:
        GuestService: A GuestService instance for use within this request.
    """
    return GuestService(session=_get_db_session())


@bp.before_request
def _require_admin() -> Response | None:
    """Reject any request to this resource that lacks an admin session.

    Returns:
        Response | None: A 401 JSON error response if the current session
        is not authenticated as an admin, otherwise None to let the
        request proceed to its view.
    """
    if not session.get("is_admin"):
        return error("Admin authentication required.", 401)
    return None


@bp.get("")
@limiter.limit("30 per minute")
def list_guests() -> Response:
    """List all guests.

    Requires an authenticated admin session.

    Returns:
        Response: 200 with a JSON array of guest records; 401 if the
        session is not an authenticated admin; 500 if the guests could
        not be retrieved.
    """
    service = get_guest_service()
    try:
        guests = service.list_guests()
        _log.debug("Listed %d guests.", len(guests))
    except SQLAlchemyError:
        _log.exception("Failed to list guests.")
        return error("Failed to list guests.", 500)

    return json(
        [GuestRead.model_validate(guest).model_dump(mode="json") for guest in guests],
        200,
    )


@bp.post("")
@limiter.limit("5 per minute")
def create_guest() -> Response:
    """Create a new guest record.

    Requires an authenticated admin session.

    Returns:
        Response: 201 with the created guest record (and a ``Location``
        header pointing at it) on success; 400 if the request body is
        missing, malformed, or fails validation; 401 if the session is
        not an authenticated admin; 500 if the record could not be
        persisted.
    """
    guest_data = parse_body(GuestCreate, request.get_json(silent=True))
    if isinstance(guest_data, Response):
        return guest_data

    service = get_guest_service()
    try:
        created_guest = service.create_guest(**guest_data.model_dump(exclude_unset=True))
        _log.debug("Created guest %d.", created_guest.id)
    except SQLAlchemyError:
        _log.exception("Failed to create guest")
        return error("Failed to create guest.", 500)

    response = json(GuestRead.model_validate(created_guest).model_dump(mode="json"), 201)
    response.headers["Location"] = url_for("guests.get_guest", guest_id=created_guest.id)
    return response


@bp.get("/<int:guest_id>")
@limiter.limit("30 per minute")
def get_guest(guest_id: int) -> Response:
    """Get a single guest by ID.

    Requires an authenticated admin session.

    Args:
        guest_id (int): The guest's unique personal ID number.

    Returns:
        Response: 200 with the guest record, or 404 if no guest with that ID
        exists; 401 if the session is not an authenticated admin; 500 if
        the guest could not be retrieved.
    """
    service = get_guest_service()
    try:
        guest = service.get_guest(guest_id)
        _log.debug("Retrieved guest %d.", guest_id)
    except SQLAlchemyError:
        _log.exception("Failed to get guest %d.", guest_id)
        return error("Failed to get guest.", 500)

    if guest is None:
        _log.error("Guest %d not found.", guest_id)
        return error("Guest not found.", 404)
    return json(GuestRead.model_validate(guest).model_dump(mode="json"), 200)


@bp.put("/<int:guest_id>")
@limiter.limit("5 per minute")
def update_guest(guest_id: int) -> Response:
    """Update an existing guest record.

    Requires an authenticated admin session.

    Args:
        guest_id (int): The unique personal ID number of the guest to update.

    Returns:
        Response: 200 with the updated guest record; 400 if the request
        body is missing, malformed, or fails validation; 401 if the
        session is not an authenticated admin; 404 if no guest with that
        ID exists; 500 if the update could not be persisted.
    """
    guest_data = parse_body(GuestUpdate, request.get_json(silent=True))
    if isinstance(guest_data, Response):
        return guest_data

    service = get_guest_service()
    try:
        updated_guest = service.update_guest(guest_id, **guest_data.model_dump(exclude_unset=True))
        _log.debug("Updated guest %d.", guest_id)
    except SQLAlchemyError:
        _log.exception("Failed to update guest %d.", guest_id)
        return error("Failed to update guest.", 500)
    except ValueError as exc:
        _log.error("Failed to update guest %d: %s", guest_id, exc)
        return error(str(exc), 400)

    if updated_guest is None:
        _log.error("Guest %d not found.", guest_id)
        return error("Guest not found.", 404)
    return json(GuestRead.model_validate(updated_guest).model_dump(mode="json"), 200)


@bp.delete("/<int:guest_id>")
@limiter.limit("5 per minute")
def delete_guest(guest_id: int) -> Response:
    """Delete a guest record.

    Requires an authenticated admin session.

    Args:
        guest_id (int): The unique personal ID number of the guest to delete.

    Returns:
        Response: 204 No Content on success; 401 if the session is not an
        authenticated admin; 404 if no guest with that ID exists; 500 if
        the deletion could not be persisted.
    """
    service = get_guest_service()
    try:
        deleted = service.delete_guest(guest_id)
        _log.debug("Deleted guest %d.", guest_id)
    except SQLAlchemyError:
        _log.exception("Failed to delete guest %d.", guest_id)
        return error("Failed to delete guest.", 500)

    if not deleted:
        _log.error("Guest %d not found.", guest_id)
        return error("Guest not found.", 404)
    return Response(status=204, mimetype="application/json")
