"""
models.guest - Pydantic models for creating, updating, and reading Guest records
--------------------------------------------------------------------------------

These models define the shape of guest data as it flows into and out of the
service layer. Field constraints (length limits, email format) mirror the
``guests`` table's column definitions (see ``db.schemas.Guest``) so that
invalid or oversized payloads are rejected with a 400 at the API boundary
rather than failing at the database layer.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from core.config import EMAIL_RE


def _validate_email_format(value: str | None) -> str | None:
    """Validate that an optional email address is in a valid format.

    Args:
        value (str | None): The email address to validate, or None.

    Returns:
        str | None: The unchanged value, if valid (or None).

    Raises:
        ValueError: If the value is not None and does not match EMAIL_RE.
    """
    if value is not None and not EMAIL_RE.match(value):
        raise ValueError(f"Invalid email address: {value}")
    return value


class GuestBase(BaseModel):
    """Fields shared by all guest models.

    Attributes:
        name (str): The guest's full name. Must be 1-120 characters.
        email (str | None): The guest's email address, if known. Must be a
            valid email format, up to 255 characters. Defaults to None.
        attending (bool | None): Whether the guest is attending. ``None`` means
            they haven't responded yet. Defaults to None.
        plus_one (bool): Whether the guest is allowed to bring a plus-one. Defaults to False.
        allergies (str | None): Free-text description of the guest's allergies,
            up to 500 characters. Defaults to None.
        food_preferences (str | None): Free-text description of the guest's food
            preferences, up to 500 characters. Defaults to None.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    attending: bool | None = None
    plus_one: bool = False
    allergies: str | None = Field(default=None, max_length=500)
    food_preferences: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        """Validate that the email address is in a valid format, if provided."""
        return _validate_email_format(value)


class GuestCreate(GuestBase):
    """Data required to create a new guest record."""


class GuestUpdate(BaseModel):
    """Partial data for updating an existing guest record.

    All fields are optional so a caller can update only the fields that
    actually changed; fields left unset are ignored by the service layer.

    Attributes:
        name (str | None): The guest's full name. Must be 1-120 characters, if provided.
        email (str | None): The guest's email address. Must be a valid email
            format, up to 255 characters, if provided.
        attending (bool | None): Whether the guest is attending.
        allergies (str | None): Free-text description of the guest's allergies,
            up to 500 characters, if provided.
        food_preferences (str | None): Free-text description of the guest's food
            preferences, up to 500 characters, if provided.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=1, max_length=120)
    email: str | None = Field(default=None, max_length=255)
    attending: bool | None = None
    allergies: str | None = Field(default=None, max_length=500)
    food_preferences: str | None = Field(default=None, max_length=500)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        """Validate that the email address is in a valid format, if provided."""
        return _validate_email_format(value)


class GuestRead(GuestBase):
    """A guest record as read back from the database.

    Attributes:
        id (int): The guest's unique personal ID number.
        created_at (datetime): When the guest record was created.
        updated_at (datetime): When the guest record was last updated.
    """

    id: int
    created_at: datetime
    updated_at: datetime
