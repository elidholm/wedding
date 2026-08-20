"""
models.guest - Pydantic models for creating, updating, and reading Guest records
--------------------------------------------------------------------------------

These models define the shape of guest data as it flows into and out of the
service layer.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GuestBase(BaseModel):
    """Fields shared by all guest models.

    Attributes:
        name (str): The guest's full name.
        email (str | None): The guest's email address, if known. Defaults to None.
        attending (bool | None): Whether the guest is attending. ``None`` means
            they haven't responded yet. Defaults to None.
        plus_one (bool): Whether the guest is allowed to bring a plus-one. Defaults to False.
        allergies (str | None): Free-text description of the guest's allergies.
            Defaults to None.
        food_preferences (str | None): Free-text description of the guest's food
            preferences. Defaults to None.
    """

    name: str
    email: str | None = None
    attending: bool | None = None
    plus_one: bool = False
    allergies: str | None = None
    food_preferences: str | None = None


class GuestCreate(GuestBase):
    """Data required to create a new guest record."""


class GuestUpdate(BaseModel):
    """Partial data for updating an existing guest record.

    All fields are optional so a caller can update only the fields that
    actually changed; fields left unset are ignored by the service layer.

    Attributes:
        name (str | None): The guest's full name.
        email (str | None): The guest's email address.
        attending (bool | None): Whether the guest is attending.
        allergies (str | None): Free-text description of the guest's allergies.
        food_preferences (str | None): Free-text description of the guest's food
            preferences.
    """

    name: str | None = None
    email: str | None = None
    attending: bool | None = None
    allergies: str | None = None
    food_preferences: str | None = None


class GuestRead(GuestBase):
    """A guest record as read back from the database.

    Attributes:
        id (int): The guest's unique personal ID number.
        created_at (datetime): When the guest record was created.
        updated_at (datetime): When the guest record was last updated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
