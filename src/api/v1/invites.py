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
from uuid import UUID

from flask import Blueprint, Response, request, session, url_for
from sqlalchemy.exc import SQLAlchemyError

from api.extensions import limiter
from api.v1.utils import error, json, parse_body
from db.schemas import Invite
from db.session import get_db_session
from models.invite import InviteCreate, InviteRead, InviteUpdate
from services.invite_service import InvalidInviteError, InviteService

_log = logging.getLogger(__name__)

bp = Blueprint("invites", __name__)


def _invite_json(invite: Invite) -> dict[str, object]:
    """Serialize an invite for an API response, including its absolute RSVP link.

    Args:
        invite (Invite): The invite record to serialize.

    Returns:
        dict[str, object]: The invite's JSON-ready fields plus ``rsvp_url``,
        the personal link to print (e.g. as a QR code) on the invitation.
    """
    payload: dict[str, object] = InviteRead.model_validate(invite).model_dump(mode="json")
    payload["rsvp_url"] = url_for("rsvp.rsvp_invite", invite_id=invite.id, _external=True)
    return payload


def get_invite_service() -> InviteService:
    """Get a InviteService bound to the current request's database session.

    Returns:
        InviteService: A InviteService instance for use within this request.
    """
    return InviteService(session=get_db_session())


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
        [_invite_json(invite) for invite in invites],
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
        _log.debug("Created invite %s.", created_invite.id)
    except SQLAlchemyError:
        _log.exception("Failed to create invite")
        return error("Failed to create invite.", 500)
    except InvalidInviteError as exc:
        _log.exception("Failed to create invite")
        return error(str(exc), 400)

    response = json(_invite_json(created_invite), 201)
    response.headers["Location"] = url_for("invites.get_invite", invite_id=created_invite.id)
    return response


@bp.get("/<uuid:invite_id>")
@limiter.limit("30 per minute")
def get_invite(invite_id: UUID) -> Response:
    """Get a single invite by ID.

    Requires an authenticated admin session.

    Args:
        invite_id (UUID): The invite's personal UUID.

    Returns:
        Response: 200 with the invite record, or 404 if no invite with that ID
        exists; 401 if the session is not an authenticated admin; 500 if
        the invite could not be retrieved.
    """
    service = get_invite_service()
    try:
        invite = service.get_invite(str(invite_id))
        _log.debug("Retrieved invite %s.", invite_id)
    except SQLAlchemyError:
        _log.exception("Failed to get invite %s.", invite_id)
        return error("Failed to get invite.", 500)

    if invite is None:
        _log.error("Invite %s not found.", invite_id)
        return error("Invite not found.", 404)
    return json(_invite_json(invite), 200)


@bp.put("/<uuid:invite_id>")
@limiter.limit("5 per minute")
def update_invite(invite_id: UUID) -> Response:
    """Update an existing invite record.

    Requires an authenticated admin session.

    Args:
        invite_id (UUID): The personal UUID of the invite to update.

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
        updated_invite = service.update_invite(str(invite_id), **invite_data.model_dump(exclude_unset=True))
        _log.debug("Updated invite %s.", invite_id)
    except SQLAlchemyError:
        _log.exception("Failed to update invite %s.", invite_id)
        return error("Failed to update invite.", 500)
    except ValueError as exc:
        _log.exception("Failed to update invite %s.", invite_id)
        return error(str(exc), 400)

    if updated_invite is None:
        _log.error("Invite %s not found.", invite_id)
        return error("Invite not found.", 404)
    return json(_invite_json(updated_invite), 200)


@bp.delete("/<uuid:invite_id>")
@limiter.limit("5 per minute")
def delete_invite(invite_id: UUID) -> Response:
    """Delete a invite record.

    Requires an authenticated admin session.

    Args:
        invite_id (UUID): The personal UUID of the invite to delete.

    Returns:
        Response: 204 No Content on success; 401 if the session is not an
        authenticated admin; 404 if no invite with that ID exists; 500 if
        the deletion could not be persisted.
    """
    service = get_invite_service()
    try:
        deleted = service.delete_invite(str(invite_id))
        _log.debug("Deleted invite %s.", invite_id)
    except SQLAlchemyError:
        _log.exception("Failed to delete invite %s.", invite_id)
        return error("Failed to delete invite.", 500)

    if not deleted:
        _log.error("Invite %s not found.", invite_id)
        return error("Invite not found.", 404)
    return Response(status=204, mimetype="application/json")
