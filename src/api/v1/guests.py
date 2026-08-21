"""
api.v1.guests - Guest API resource
----------------------------------

This module defines the API resource for managing guest records. It
provides endpoints for listing, creating, retrieving, updating, and
deleting guests.

Every response - success or error - is JSON, including validation
failures (400), not-found (404), and method-not-allowed (405) errors, so
API consumers never have to deal with Flask's default HTML error pages.

There is no authentication/authorization on these endpoints yet - that is
planned for a future change, once an admin role exists.
"""

import logging

from flask import Blueprint, Response, g, jsonify, request, url_for
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

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


def _json(payload: object, status: int) -> Response:
    """Build a JSON response with an explicit status code.

    Args:
        payload (object): The JSON-serializable payload to return.
        status (int): The HTTP status code for the response.

    Returns:
        Response: The resulting Flask response.
    """
    response = jsonify(payload)
    response.status_code = status
    return response


def _error(message: str, status: int, **extra: object) -> Response:
    """Build a JSON error response of the shape ``{"error": message, **extra}``.

    Args:
        message (str): A human-readable error message.
        status (int): The HTTP status code for the response.
        **extra (object): Any additional fields to merge into the error body
            (e.g. ``details`` for validation errors).

    Returns:
        Response: The resulting Flask error response.
    """
    return _json({"error": message, **extra}, status)


def _parse_body(model: type[GuestCreate] | type[GuestUpdate], payload: object) -> GuestCreate | GuestUpdate | Response:
    """Validate a request's JSON body against a guest pydantic model.

    Args:
        model (type[GuestCreate] | type[GuestUpdate]): The model to validate against.
        payload (object): The parsed JSON body (or None if missing/invalid JSON).

    Returns:
        GuestCreate | GuestUpdate | Response: The validated model instance,
        or a ready-to-return 400 error Response if the body was missing,
        not valid JSON, or failed validation.
    """
    if payload is None:
        return _error("Request body must be valid JSON.", 400)

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        return _error("Invalid request data.", 400, details=exc.errors(include_url=False, include_context=False))


@bp.get("")
def list_guests() -> Response:
    """List all guests.

    Returns:
        Response: 200 with a JSON array of guest records; 500 if the
        guests could not be retrieved.
    """
    service = get_guest_service()
    try:
        guests = service.list_guests()
    except SQLAlchemyError:
        _log.exception("Failed to list guests.")
        return _error("Failed to list guests.", 500)
    return _json([GuestRead.model_validate(guest).model_dump(mode="json") for guest in guests], 200)


@bp.post("")
def create_guest() -> Response:
    """Create a new guest record.

    Returns:
        Response: 201 with the created guest record (and a ``Location``
        header pointing at it) on success; 400 if the request body is
        missing, malformed, or fails validation; 500 if the record could
        not be persisted.
    """
    guest_data = _parse_body(GuestCreate, request.get_json(silent=True))
    if isinstance(guest_data, Response):
        return guest_data

    service = get_guest_service()
    try:
        created_guest = service.create_guest(**guest_data.model_dump(exclude_unset=True))
    except SQLAlchemyError:
        _log.exception("Failed to create guest.")
        return _error("Failed to create guest.", 500)

    response = _json(GuestRead.model_validate(created_guest).model_dump(mode="json"), 201)
    response.headers["Location"] = url_for("guests.get_guest", guest_id=created_guest.id)
    return response


@bp.get("/<int:guest_id>")
def get_guest(guest_id: int) -> Response:
    """Get a single guest by ID.

    Args:
        guest_id (int): The guest's unique personal ID number.

    Returns:
        Response: 200 with the guest record, or 404 if no guest with that ID
        exists; 500 if the guest could not be retrieved.
    """
    service = get_guest_service()
    try:
        guest = service.get_guest(guest_id)
    except SQLAlchemyError:
        _log.exception("Failed to get guest %s.", guest_id)
        return _error("Failed to get guest.", 500)
    if guest is None:
        return _error("Guest not found.", 404)
    return _json(GuestRead.model_validate(guest).model_dump(mode="json"), 200)


@bp.put("/<int:guest_id>")
def update_guest(guest_id: int) -> Response:
    """Update an existing guest record.

    Args:
        guest_id (int): The unique personal ID number of the guest to update.

    Returns:
        Response: 200 with the updated guest record; 400 if the request
        body is missing, malformed, or fails validation; 404 if no guest
        with that ID exists; 500 if the update could not be persisted.
    """
    guest_data = _parse_body(GuestUpdate, request.get_json(silent=True))
    if isinstance(guest_data, Response):
        return guest_data

    service = get_guest_service()
    try:
        updated_guest = service.update_guest(guest_id, **guest_data.model_dump(exclude_unset=True))
    except SQLAlchemyError:
        _log.exception("Failed to update guest %s.", guest_id)
        return _error("Failed to update guest.", 500)

    if updated_guest is None:
        return _error("Guest not found.", 404)
    return _json(GuestRead.model_validate(updated_guest).model_dump(mode="json"), 200)


@bp.delete("/<int:guest_id>")
def delete_guest(guest_id: int) -> Response:
    """Delete a guest record.

    Args:
        guest_id (int): The unique personal ID number of the guest to delete.

    Returns:
        Response: 204 No Content on success; 404 if no guest with that ID
        exists; 500 if the deletion could not be persisted.
    """
    service = get_guest_service()
    try:
        deleted = service.delete_guest(guest_id)
    except SQLAlchemyError:
        _log.exception("Failed to delete guest %s.", guest_id)
        return _error("Failed to delete guest.", 500)

    if not deleted:
        return _error("Guest not found.", 404)
    return Response(status=204, mimetype="application/json")
