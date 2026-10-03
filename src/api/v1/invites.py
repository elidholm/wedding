"""
api.v1.invites - Invite API resource
------------------------------------

This module defines the API resource for managing invite records. It
provides endpoints for listing, creating, retrieving, updating, and
deleting invites.

Invite records are personal data (names, emails, allergies, food
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
from models.invite import InviteCreate, InviteRead, InviteUpdate
from services.invite_service import InvalidInviteError, InviteService

_log = logging.getLogger(__name__)

bp = Blueprint("invites", __name__)


def _get_db_session() -> Session:
    """Get (or lazily open) the current request's SQLAlchemy session.

    The session is stashed on Flask's request-scoped ``g`` object so every
    call within the same request reuses it, and is closed automatically by
    ``_close_db_session`` once the request tears down.

    Returns:
        Session: The current request's SQLAlchemy session.
    """
    if "invites_db_session" not in g:
        g.invites_db_session = SessionLocal()
    return g.invites_db_session


@bp.teardown_request
def _close_db_session(exception: BaseException | None = None) -> None:
    """Close this request's database session, rolling back first on error.

    Args:
        exception (BaseException | None): The exception that ended the
            request, if any, as passed by Flask's ``teardown_request`` hook.
    """
    session = g.pop("invites_db_session", None)
    if session is not None:
        if exception is not None:
            session.rollback()
        session.close()


def get_invite_service() -> InviteService:
    """Get a InviteService bound to the current request's database session.

    Returns:
        InviteService: A InviteService instance for use within this request.
    """
    return InviteService(session=_get_db_session())


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
def list_invites() -> Response:
    """List all invites.

    Requires an authenticated admin session.

    Returns:
        Response: 200 with a JSON array of invite records; 401 if the
        session is not an authenticated admin; 500 if the invites could
        not be retrieved.
    """
    service = get_invite_service()
    try:
        invites = service.list_invites()
        _log.debug("Listed %d invites.", len(invites))
    except SQLAlchemyError:
        _log.exception("Failed to list invites.")
        return error("Failed to list invites.", 500)

    return json(
        [InviteRead.model_validate(invite).model_dump(mode="json") for invite in invites],
        200,
    )


@bp.post("")
@limiter.limit("5 per minute")
def create_invite() -> Response:
    """Create a new invite record.

    Requires an authenticated admin session.

    Returns:
        Response: 201 with the created invite record (and a ``Location``
        header pointing at it) on success; 400 if the request body is
        missing, malformed, or fails validation; 401 if the session is
        not an authenticated admin; 500 if the record could not be
        persisted.
    """
    invite_data = parse_body(InviteCreate, request.get_json(silent=True))
    if isinstance(invite_data, Response):
        return invite_data

    service = get_invite_service()
    try:
        created_invite = service.create_invite(**invite_data.model_dump(exclude_unset=True))
        _log.debug("Created invite %d.", created_invite.id)
    except SQLAlchemyError:
        _log.exception("Failed to create invite")
        return error("Failed to create invite.", 500)
    except InvalidInviteError as exc:
        _log.error("Failed to create invite: %s", exc)
        return error(str(exc), 400)

    response = json(InviteRead.model_validate(created_invite).model_dump(mode="json"), 201)
    response.headers["Location"] = url_for("invites.get_invite", invite_id=created_invite.id)
    return response


@bp.get("/<int:invite_id>")
@limiter.limit("30 per minute")
def get_invite(invite_id: int) -> Response:
    """Get a single invite by ID.

    Requires an authenticated admin session.

    Args:
        invite_id (int): The invite's unique personal ID number.

    Returns:
        Response: 200 with the invite record, or 404 if no invite with that ID
        exists; 401 if the session is not an authenticated admin; 500 if
        the invite could not be retrieved.
    """
    service = get_invite_service()
    try:
        invite = service.get_invite(invite_id)
        _log.debug("Retrieved invite %d.", invite_id)
    except SQLAlchemyError:
        _log.exception("Failed to get invite %d.", invite_id)
        return error("Failed to get invite.", 500)

    if invite is None:
        _log.error("Invite %d not found.", invite_id)
        return error("Invite not found.", 404)
    return json(InviteRead.model_validate(invite).model_dump(mode="json"), 200)


@bp.put("/<int:invite_id>")
@limiter.limit("5 per minute")
def update_invite(invite_id: int) -> Response:
    """Update an existing invite record.

    Requires an authenticated admin session.

    Args:
        invite_id (int): The unique personal ID number of the invite to update.

    Returns:
        Response: 200 with the updated invite record; 400 if the request
        body is missing, malformed, or fails validation; 401 if the
        session is not an authenticated admin; 404 if no invite with that
        ID exists; 500 if the update could not be persisted.
    """
    invite_data = parse_body(InviteUpdate, request.get_json(silent=True))
    if isinstance(invite_data, Response):
        return invite_data

    service = get_invite_service()
    try:
        updated_invite = service.update_invite(invite_id, **invite_data.model_dump(exclude_unset=True))
        _log.debug("Updated invite %d.", invite_id)
    except SQLAlchemyError:
        _log.exception("Failed to update invite %d.", invite_id)
        return error("Failed to update invite.", 500)
    except ValueError as exc:
        _log.error("Failed to update invite %d: %s", invite_id, exc)
        return error(str(exc), 400)

    if updated_invite is None:
        _log.error("Invite %d not found.", invite_id)
        return error("Invite not found.", 404)
    return json(InviteRead.model_validate(updated_invite).model_dump(mode="json"), 200)


@bp.delete("/<int:invite_id>")
@limiter.limit("5 per minute")
def delete_invite(invite_id: int) -> Response:
    """Delete a invite record.

    Requires an authenticated admin session.

    Args:
        invite_id (int): The unique personal ID number of the invite to delete.

    Returns:
        Response: 204 No Content on success; 401 if the session is not an
        authenticated admin; 404 if no invite with that ID exists; 500 if
        the deletion could not be persisted.
    """
    service = get_invite_service()
    try:
        deleted = service.delete_invite(invite_id)
        _log.debug("Deleted invite %d.", invite_id)
    except SQLAlchemyError:
        _log.exception("Failed to delete invite %d.", invite_id)
        return error("Failed to delete invite.", 500)

    if not deleted:
        _log.error("Invite %d not found.", invite_id)
        return error("Invite not found.", 404)
    return Response(status=204, mimetype="application/json")
