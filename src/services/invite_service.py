"""
services.invite_service - Service layer for invite CRUD operations
------------------------------------------------------------------

``InviteService`` wraps a SQLAlchemy ``Session`` and exposes invite management operations.
"""

import logging
from collections.abc import Iterable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.schemas import Guest, Invite
from services.guest_service import GuestService

_log = logging.getLogger(__name__)


class InvalidInviteError(ValueError):
    """Raised when an invite is invalid, e.g. when it references a guest that does not exist."""


class InviteService:
    """Service for creating, reading, updating, and deleting invite records.

    Args:
        session (Session): The SQLAlchemy session to use for all database
            operations performed by this service.
    """

    def __init__(self, session: Session) -> None:
        self._db = session
        self._guest_service = GuestService(session)

    def list_invites(self) -> list[Invite]:
        """List every invite in the database.

        Returns:
            list[Invite]: All invite records.
        """
        return self._db.query(Invite).all()

    def get_invite(self, invite_id: int) -> Invite | None:
        """Get a single invite by ID.

        Args:
            invite_id (int): The invite's unique personal ID number.

        Returns:
            Invite | None: The matching invite record, or None if no invite
            with that ID exists.
        """
        return self._db.query(Invite).filter(Invite.id == invite_id).first()

    def create_invite(
        self,
        guest_ids: list[int] | None = None,
        housing_needs: str | None = None,
    ) -> Invite:
        """Create a new invite record.

        Args:
            guest_ids (list[int] | None): IDs of guests associated with this invite.
                Defaults to an empty list.
            housing_needs (str | None): Free-text description of the invite's housing
                needs, if any. Must be at most 500 characters.

        Returns:
            Invite: The newly created invite record.

        Raises:
            SQLAlchemyError: If the record could not be persisted. The
                session is rolled back before this is re-raised.
        """
        if guest_ids is None:
            guest_ids = []

        guests = self._get_guests(guest_ids)

        invite = Invite(
            guests=guests or [],
            housing_needs=housing_needs,
        )
        self._db.add(invite)
        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        self._db.refresh(invite)
        return invite

    def update_invite(
        self,
        invite_id: int,
        guest_ids: list[int] | None = None,
        clear_guests: bool | None = None,
        housing_needs: str | None = None,
        clear_housing_needs: bool | None = None,
    ) -> Invite | None:
        """Update an existing invite record.

        Leaving any argument as None will leave that field unchanged.

        Args:
            invite_id (int): The unique ID number of the invite to update.
            guest_ids (list[int] | None): The guests included in this invite.
                Defaults to None.
            clear_guests (bool | None): If True, clear the guests in the invite.
                Defaults to None.
            housing_needs (str | None): The housing needs expressed by the
                invitees. Defaults to None.
            clear_housing_needs (bool | None): If True, clear the housing needs
                of this invite. Defaults to None.

        Returns:
            Invite | None: The updated invite record, or None if no invite with that ID
            exists.

        Raises:
            SQLAlchemyError: If the update could not be persisted. The
                session is rolled back before this is re-raised.
        """
        invite = self.get_invite(invite_id)
        if not invite:
            return None

        if clear_guests:
            if guest_ids is not None:
                _log.warning("Ignoring guests because clear_guests is True.")
            invite.guests = []
        elif guest_ids is not None:
            invite.guests = self._get_guests(guest_ids)

        if clear_housing_needs:
            if housing_needs is not None:
                _log.warning("Ignoring housing_needs because clear_housing_needs is True.")
            invite.housing_needs = None
        elif housing_needs is not None:
            invite.housing_needs = housing_needs

        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        self._db.refresh(invite)
        return invite

    def delete_invite(self, invite_id: int) -> bool:
        """Delete an invite record.

        Args:
            invite_id (int): The unique ID number of the invite to delete.

        Returns:
            bool: True if an invite was deleted, False if no invite with that ID
            existed.
            SQLAlchemyError: If the deletion could not be persisted. The
                session is rolled back before this is re-raised.
        """
        invite = self.get_invite(invite_id)
        if not invite:
            return False

        self._db.delete(invite)
        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        return True

    def _get_guests(self, guest_ids: Iterable[int]) -> list[Guest]:
        """Get a list of Guest objects for the given guest IDs.

        Args:
            guest_ids (Iterable[int]): The IDs of the guests to fetch.

        Returns:
            list[Guest]: The matching Guest objects.

        Raises:
            InvalidInviteError: If any of the given guest IDs do not exist.
        """
        guests: list[Guest] = []
        not_found: list[str] = []
        for id in guest_ids:
            if guest := self._guest_service.get_guest(id):
                guests.append(guest)
                continue

            not_found.append(str(id))

        if not_found:
            raise InvalidInviteError(
                f"Guest{'s' if len(not_found) > 1 else ''} {', '.join(not_found)} "
                f"do{'es' if len(not_found) == 1 else ''} not exist."
            )

        return guests
