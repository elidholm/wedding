"""
api.v1.guests - Guest API resource
----------------------------------

This module defines the API resource for managing guest records. It
provides endpoints for listing, creating, retrieving, updating, and
deleting guests.
"""

from flask import Blueprint, request

from db.schemas import SessionLocal
from models.guest import GuestCreate, GuestRead, GuestUpdate
from services.guest_service import GuestService

bp = Blueprint("guests", __name__)


def get_guest_service() -> GuestService:
    """Get a new instance of GuestService using the current request's database session.

    Returns:
        GuestService: A new instance of GuestService.
    """
    return GuestService(session=SessionLocal())


@bp.get("")
def list_guests() -> tuple[list[dict], int]:
    service = get_guest_service()
    guests = service.list_guests()
    return [GuestRead.model_validate(guest).model_dump() for guest in guests], 200


@bp.post("")
def create_guest() -> tuple[dict, int]:
    guest = GuestCreate.model_validate(request.get_json())
    service = get_guest_service()
    created_guest = service.create_guest(**guest.model_dump(exclude_unset=True))
    return GuestRead.model_validate(created_guest).model_dump(), 200


@bp.get("/<int:guest_id>")
def get_guest(guest_id: int) -> tuple[dict, int]:
    service = get_guest_service()
    guest = service.get_guest(guest_id)
    if guest is None:
        return {"error": "Guest not found"}, 404
    return GuestRead.model_validate(guest).model_dump(), 200


@bp.put("/<int:guest_id>")
def update_guest(guest_id: int) -> tuple[dict, int]:
    guest_data = GuestUpdate.model_validate(request.get_json())
    service = get_guest_service()
    updated_guest = service.update_guest(guest_id, **guest_data.model_dump(exclude_unset=True))
    if updated_guest is None:
        return {"error": "Guest not found"}, 404
    return GuestRead.model_validate(updated_guest).model_dump(), 200


@bp.delete("/<int:guest_id>")
def delete_guest(guest_id: int) -> tuple[dict, int]:
    service = get_guest_service()
    success = service.delete_guest(guest_id)
    if not success:
        return {"error": "Guest not found"}, 404
    return {"success": True}, 200
