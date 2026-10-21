"""
db.seed - Seed clearly fake invites for local development
---------------------------------------------------------

Run from the repository root with ``make seed`` (``PYTHONPATH=src uv run
python -m db.seed``). Seeding is idempotent: each fake invite has a fixed
UUID, so its RSVP link stays the same across runs and re-running the seed
never creates duplicates. Never add real guest data here.
"""

from sqlalchemy.orm import Session

from core.config import get_config
from db.schemas import Base, Guest, Invite, SessionLocal, engine

FAKE_INVITES: dict[str, list[dict[str, object]]] = {
    "00000000-0000-4000-8000-000000000001": [
        {"name": "Alex Example", "plus_one_allowed": True},
        {"name": "Robin Example"},
    ],
    "00000000-0000-4000-8000-000000000002": [
        {"name": "Sam Example"},
    ],
}


def seed(session: Session) -> list[Invite]:
    """Insert every fake invite (and its guests) that doesn't exist yet.

    Args:
        session (Session): The SQLAlchemy session to seed through.

    Returns:
        list[Invite]: Every fake invite, whether newly created or existing.
    """
    invites = []
    for invite_id, guests in FAKE_INVITES.items():
        invite = session.get(Invite, invite_id)
        if invite is None:
            invite = Invite(id=invite_id, guests=[Guest(**guest) for guest in guests])
            session.add(invite)
        invites.append(invite)
    session.commit()
    return invites


def main() -> None:
    """Create the tables if needed, seed the fake invites, and print their RSVP links."""
    config = get_config()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        for invite in seed(session):
            names = ", ".join(guest.name for guest in invite.guests)
            print(f"http://localhost:{config.port}/rsvp/{invite.id}  ({names})")


if __name__ == "__main__":
    main()
