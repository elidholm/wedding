"""
db.schemas - SQLAlchemy engine, session factory, and declarative table schemas
------------------------------------------------------------------------------
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from core.config import get_config

config = get_config()

engine = create_engine(config.db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class shared by every ORM table schema in this module."""


class Guest(Base):
    """ORM table schema for a wedding guest/invitee.

    Attributes:
        id (int): The guest's unique personal ID number (primary key), matching
            the ID printed on their invite.
        name (str): The guest's full name.
        email (str | None): The guest's email address, if known.
        attending (bool | None): Whether the guest is attending. ``None`` means
            they haven't responded yet.
        plus_one_allowed (bool): Whether the guest is allowed to bring a plus-one. Defaults to False.
        plus_one_name (str | None): The name of the guest's plus-one, if any.
        food_preferences (str | None): Free-text description of the guest's food
            preferences.
        invite_id (int | None): The ID of the invite associated with this guest, if any.
        invite (Invite): The Invite object associated with this guest, if any.
        created_at (datetime): When the guest record was created.
        updated_at (datetime): When the guest record was last updated.
    """

    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attending: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    plus_one_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    plus_one_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    food_preferences: Mapped[str | None] = mapped_column(String(500), nullable=True)

    invite_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("invites.id"), nullable=True)
    invite: Mapped["Invite"] = relationship("Invite")

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<Guest(id={self.id}, name={self.name}, email={self.email})>"


class Invite(Base):
    """ORM table schema for a wedding invite.

    Attributes:
        id (int): The invite's unique ID number (primary key).
        guests (list[Guest]): The list of guests associated with this invite.
        housing_needs (str | None): Free-text description of the invite's housing
            needs, if any.
        created_at (datetime): When the invite record was created.
        updated_at (datetime): When the invite record was last updated.
    """

    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guests: Mapped[list[Guest]] = relationship("Guest", back_populates="invite")
    housing_needs: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self) -> str:
        return f"<Invite(id={self.id}, guests={[guest.name for guest in self.guests]})>"
