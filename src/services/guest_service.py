"""
services.guest_service - Service layer for guest CRUD operations
----------------------------------------------------------------

``GuestService`` wraps a SQLAlchemy ``Session`` and exposes guest management operations.
"""

import logging

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.schemas import Guest

_log = logging.getLogger(__name__)


class GuestService:
    """Service for creating, reading, updating, and deleting guest records.

    Args:
        session (Session): The SQLAlchemy session to use for all database
            operations performed by this service.
    """

    def __init__(self, session: Session) -> None:
        self._db = session

    def list_guests(self) -> list[Guest]:
        """List every guest in the database.

        Returns:
            list[Guest]: All guest records.
        """
        return self._db.query(Guest).all()

    def get_guest(self, guest_id: int) -> Guest | None:
        """Get a single guest by ID.

        Args:
            guest_id (int): The guest's unique personal ID number.

        Returns:
            Guest | None: The matching guest record, or None if no guest
            with that ID exists.
        """
        return self._db.query(Guest).filter(Guest.id == guest_id).first()

    def create_guest(
        self,
        name: str,
        email: str | None = None,
        attending: bool | None = None,
        plus_one_allowed: bool = False,
        plus_one_name: str | None = None,
        food_preferences: str | None = None,
    ) -> Guest:
        """Create a new guest record.

        Args:
            name (str): The guest's full name.
            email (str | None): The guest's email address, if known. Defaults to None.
            attending (bool | None): Whether the guest is attending. Defaults to None.
            plus_one_allowed (bool): Whether the guest is allowed to bring a
                plus-one. Defaults to False.
            plus_one_name (str | None): The name of the guest's plus-one, if any.
            food_preferences (str | None): Free-text description of the guest's food
                preferences. Defaults to None.

        Returns:
            Guest: The newly created guest record.

        Raises:
            SQLAlchemyError: If the record could not be persisted. The
                session is rolled back before this is re-raised.
        """
        if not plus_one_allowed and plus_one_name:
            _log.warning(
                "Guest is not allowed to bring a plus-one, but a plus-one name was provided. Ignoring plus-one name."
            )
            plus_one_name = None

        guest = Guest(
            name=name,
            email=email,
            attending=attending,
            plus_one_allowed=plus_one_allowed,
            plus_one_name=plus_one_name,
            food_preferences=food_preferences,
        )
        self._db.add(guest)
        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        self._db.refresh(guest)
        return guest

    def update_guest(
        self,
        guest_id: int,
        name: str | None = None,
        email: str | None = None,
        attending: bool | None = None,
        plus_one_allowed: bool | None = None,
        plus_one_name: str | None = None,
        clear_plus_one_name: bool | None = None,
        food_preferences: str | None = None,
        clear_food_preferences: bool | None = None,
    ) -> Guest | None:
        """Update an existing guest record.

        Leaving any argument as None will leave that field unchanged.

        Args:
            guest_id (int): The unique personal ID number of the guest to
                update.
            name (str | None): The guest's full name. Defaults to None.
            email (str | None): The guest's email address. Defaults to None.
            attending (bool | None): Whether the guest is attending. Defaults to None.
            plus_one_allowed (bool | None): Whether the guest is allowed to bring a
                plus-one. Defaults to None.
            plus_one_name (str | None): The name of the guest's plus-one, if any. Defaults
                to None.
            clear_plus_one_name (bool | None): If True, clears the guest's plus-one name.
            food_preferences (str | None): Free-text description of the guest's food
                preferences. Defaults to None.
            clear_food_preferences (bool | None): If True, clears the guest's food preferences.

        Returns:
            Guest | None: The updated guest record, or None if no guest with that ID
            exists.

        Raises:
            ValueError: If plus_one_name is provided but plus_one_allowed is False.
            SQLAlchemyError: If the update could not be persisted. The
                session is rolled back before this is re-raised.
        """
        guest = self.get_guest(guest_id)
        if not guest:
            return None

        if name is not None:
            guest.name = name

        if email is not None:
            guest.email = email

        if attending is not None:
            guest.attending = attending

        if plus_one_allowed is not None:
            guest.plus_one_allowed = plus_one_allowed
            if not plus_one_allowed and guest.plus_one_name:
                _log.warning(
                    "Guest %d is no longer allowed to bring a plus-one, but they have a plus-one name. "
                    "Clearing plus-one name.",
                    guest_id,
                )
                guest.plus_one_name = None

        if clear_plus_one_name:
            if plus_one_name is not None:
                _log.warning("Ignoring plus_one_name because clear_plus_one_name is True.")
            guest.plus_one_name = None
        elif plus_one_name is not None:
            if not guest.plus_one_allowed:
                _log.error("Guest %d is not allowed to bring a plus-one, but a plus-one name was provided.", guest_id)
                raise ValueError("Plus-one not allowed.")
            guest.plus_one_name = plus_one_name

        if clear_food_preferences:
            if food_preferences is not None:
                _log.warning("Ignoring food_preferences because clear_food_preferences is True.")
            guest.food_preferences = None
        elif food_preferences is not None:
            guest.food_preferences = food_preferences

        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        self._db.refresh(guest)
        return guest

    def delete_guest(self, guest_id: int) -> bool:
        """Delete a guest record.

        Args:
            guest_id (int): The unique personal ID number of the guest to
                delete.

        Returns:
            bool: True if a guest was deleted, False if no guest with that ID
            existed.

        Raises:
            SQLAlchemyError: If the deletion could not be persisted. The
                session is rolled back before this is re-raised.
        """
        guest = self.get_guest(guest_id)
        if not guest:
            return False

        self._db.delete(guest)
        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        return True
