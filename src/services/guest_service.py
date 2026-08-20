"""
services.guest_service - Service layer for guest CRUD operations
----------------------------------------------------------------

``GuestService`` wraps a SQLAlchemy ``Session`` and exposes guest management operations.
"""

from sqlalchemy.orm import Session

from db.schemas import Guest


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

    def create_guest(self, name: str, plus_one: bool) -> Guest:
        """Create a new guest record.

        Args:
            name (str): The guest's full name.
            plus_one (bool): Whether the guest is allowed to bring a plus-one.

        Returns:
            Guest: The newly created guest record.
        """
        guest = Guest(name=name, plus_one=plus_one)
        self._db.add(guest)
        self._db.commit()
        self._db.refresh(guest)
        return guest

    def update_guest(
        self, guest_id: int, name: str, email: str, attending: bool, allergies: str, food_preferences: str
    ) -> Guest | None:
        """Update an existing guest record.

        Args:
            guest_id (int): The unique personal ID number of the guest to
                update.
            name (str): The guest's full name.
            email (str): The guest's email address.
            attending (bool): Whether the guest is attending.
            allergies (str): Free-text description of the guest's allergies.
            food_preferences (str): Free-text description of the guest's food
                preferences.

        Returns:
            Guest | None: The updated guest record, or None if no guest with
            that ID exists.
        """
        guest = self.get_guest(guest_id)
        if not guest:
            return None

        guest.name = name
        guest.email = email
        guest.attending = attending
        guest.allergies = allergies
        guest.food_preferences = food_preferences

        self._db.commit()
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
        """
        guest = self.get_guest(guest_id)
        if not guest:
            return False

        self._db.delete(guest)
        self._db.commit()
        return True
