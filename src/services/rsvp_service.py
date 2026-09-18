"""In-memory RSVP data and validation for the guest-facing RSVP flow."""

from dataclasses import dataclass
from threading import Lock


@dataclass
class RsvpGuest:
    """A fake invitee record used for local development and testing."""

    guest_id: str
    name: str
    plus_one_allowed: bool = False
    attending: bool | None = None
    plus_one_name: str = ""
    dietary_requirements: str = ""
    housing_needs: str = ""


_guests = {
    "123456": RsvpGuest("123456", "Alex Andersson", plus_one_allowed=True),
    "654321": RsvpGuest("654321", "Robin Berg", plus_one_allowed=False),
}
_lock = Lock()


def find_guest(guest_id: str) -> RsvpGuest | None:
    """Return a fake invitee by their six-digit invitation ID."""
    return _guests.get(guest_id)


def save_rsvp(guest_id: str, values: dict[str, str]) -> RsvpGuest | None:
    """Validate and save an RSVP response, returning the updated guest."""
    guest = find_guest(guest_id)
    if guest is None:
        return None

    attending = values.get("attending", "")
    if attending not in {"yes", "no"}:
        raise ValueError("Välj om du kommer på bröllopet.")

    plus_one_name = values.get("plus_one_name", "").strip()
    bringing_plus_one = values.get("bringing_plus_one", "")
    if attending == "no" or not guest.plus_one_allowed:
        plus_one_name = ""
    elif bringing_plus_one == "yes":
        if not plus_one_name:
            raise ValueError("Ange namnet på din medföljande gäst.")
    else:
        plus_one_name = ""

    dietary_requirements = values.get("dietary_requirements", "").strip()
    housing_needs = values.get("housing_needs", "").strip()
    if len(dietary_requirements) > 500 or len(housing_needs) > 500:
        raise ValueError("Svaren får vara högst 500 tecken.")

    with _lock:
        guest.attending = attending == "yes"
        guest.plus_one_name = plus_one_name
        guest.dietary_requirements = dietary_requirements
        guest.housing_needs = housing_needs
    return guest
