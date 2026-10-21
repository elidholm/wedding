"""
services.rsvp_service - Service layer for the guest-facing RSVP flow
--------------------------------------------------------------------

``RsvpService`` wraps a SQLAlchemy ``Session`` and lets an invite's guests
answer the RSVP form: per-guest attendance, plus-one, food preferences, and
email, plus the invite-level housing needs. Every submission is validated in
full before anything is changed, then saved in a single commit.
"""

import logging
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core.config import EMAIL_RE
from db.schemas import Guest, Invite

_log = logging.getLogger(__name__)

NAME_MAX_LENGTH = 120
EMAIL_MAX_LENGTH = 255
TEXT_MAX_LENGTH = 500


def guest_field(guest_id: int, field: str) -> str:
    """Build the RSVP form field name for one guest's answer.

    Args:
        guest_id (int): The ID of the guest the field belongs to.
        field (str): The field's base name, e.g. ``"attending"``.

    Returns:
        str: The namespaced form field name, e.g. ``"guest-7-attending"``.
    """
    return f"guest-{guest_id}-{field}"


@dataclass(frozen=True)
class _GuestAnswer:
    """A single guest's validated RSVP answer, ready to be applied."""

    guest: Guest
    attending: bool | None
    plus_one_name: str | None
    food_preferences: str | None
    email: str | None


class RsvpService:
    """Service for reading invites and saving their guests' RSVP answers.

    Args:
        session (Session): The SQLAlchemy session to use for all database
            operations performed by this service.
    """

    def __init__(self, session: Session) -> None:
        self._db = session

    def get_invite(self, invite_id: str) -> Invite | None:
        """Get a single invite by its UUID.

        Args:
            invite_id (str): The invite's UUID.

        Returns:
            Invite | None: The matching invite, or None if it doesn't exist.
        """
        return self._db.get(Invite, invite_id)

    def save_rsvp(self, invite_id: str, values: Mapping[str, str]) -> Invite | None:
        """Validate and save an invite's RSVP form submission.

        A guest whose attendance is left unanswered keeps their previous
        answer (None if they never answered). Blank optional fields are
        stored as None.

        Args:
            invite_id (str): The UUID of the invite being answered.
            values (Mapping[str, str]): The submitted form values, using
                ``guest_field`` names for per-guest answers and
                ``housing_needs`` for the invite-level answer.

        Returns:
            Invite | None: The updated invite, or None if it doesn't exist.

        Raises:
            ValueError: If any answer is invalid. Nothing is saved.
            SQLAlchemyError: If the answers could not be persisted. The
                session is rolled back before this is re-raised.
        """
        invite = self.get_invite(invite_id)
        if invite is None:
            return None

        answers = [_parse_guest_answer(guest, values) for guest in invite.guests]
        housing_needs = _optional_text(values.get("housing_needs", ""), "Boendebehov")

        for answer in answers:
            answer.guest.attending = answer.attending
            answer.guest.plus_one_name = answer.plus_one_name
            answer.guest.food_preferences = answer.food_preferences
            answer.guest.email = answer.email
        invite.housing_needs = housing_needs

        try:
            self._db.commit()
        except SQLAlchemyError:
            self._db.rollback()
            raise
        self._db.refresh(invite)
        _log.debug("Saved RSVP for invite %s.", invite_id)
        return invite


def _parse_guest_answer(guest: Guest, values: Mapping[str, str]) -> _GuestAnswer:
    """Validate one guest's part of an RSVP submission.

    Args:
        guest (Guest): The guest being answered for.
        values (Mapping[str, str]): The submitted form values.

    Returns:
        _GuestAnswer: The guest's validated answer.

    Raises:
        ValueError: If any of the guest's answers is invalid.
    """
    attending_value = values.get(guest_field(guest.id, "attending"), "")
    if attending_value not in {"", "yes", "no"}:
        raise ValueError(f"Välj om {guest.name} kommer på bröllopet.")
    attending = guest.attending if attending_value == "" else attending_value == "yes"

    plus_one_name = None
    bringing_plus_one = values.get(guest_field(guest.id, "bringing_plus_one"), "") == "yes"
    if guest.plus_one_allowed and attending is not False and bringing_plus_one:
        plus_one_name = values.get(guest_field(guest.id, "plus_one_name"), "").strip()
        if not plus_one_name:
            raise ValueError(f"Ange namnet på medföljande gäst till {guest.name}.")
        if len(plus_one_name) > NAME_MAX_LENGTH:
            raise ValueError(f"Namnet på medföljande gäst får vara högst {NAME_MAX_LENGTH} tecken.")

    food_preferences = _optional_text(values.get(guest_field(guest.id, "food_preferences"), ""), "Specialkost")

    email = values.get(guest_field(guest.id, "email"), "").strip() or None
    if email is not None and (len(email) > EMAIL_MAX_LENGTH or not EMAIL_RE.match(email)):
        raise ValueError(f"Ange en giltig e-postadress för {guest.name}.")

    return _GuestAnswer(guest, attending, plus_one_name, food_preferences, email)


def _optional_text(value: str, label: str) -> str | None:
    """Validate an optional free-text answer.

    Args:
        value (str): The submitted text.
        label (str): A human-readable (Swedish) name for the field, used in errors.

    Returns:
        str | None: The stripped text, or None if it was blank.

    Raises:
        ValueError: If the text is longer than ``TEXT_MAX_LENGTH``.
    """
    text = value.strip()
    if len(text) > TEXT_MAX_LENGTH:
        raise ValueError(f"{label} får vara högst {TEXT_MAX_LENGTH} tecken.")
    return text or None
