"""
db.schemas - SQLAlchemy engine, session factory, and declarative table schemas
------------------------------------------------------------------------------
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

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
        plus_ones (bool): Whether the guest is allowed to bring a plus-one. Defaults to False.
        allergies (str | None): Free-text description of the guest's allergies.
        food_preferences (str | None): Free-text description of the guest's food
            preferences.
        created_at (datetime): When the guest record was created.
        updated_at (datetime): When the guest record was last updated.
    """

    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attending: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    plus_one: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    allergies: Mapped[str | None] = mapped_column(String(500), nullable=True)
    food_preferences: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
