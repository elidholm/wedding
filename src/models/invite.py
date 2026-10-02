"""
models.invite - Pydantic models for creating, updating, and reading Invite records
----------------------------------------------------------------------------------

These models define the shape of invite data as it flows into and out of the
service layer.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.guest import GuestRead


class InviteBase(BaseModel):
    """Fields shared by all invite models.

    Attributes:
        housing_needs (str | None): Free-text description of the invite's housing
            needs, if any. Must be at most 500 characters.
    """

    model_config = ConfigDict(from_attributes=True)

    housing_needs: str | None = Field(default=None, max_length=500)


class InviteCreate(InviteBase):
    """Data required to create a new invite record.

    Attributes:
        guest_ids (list[int]): IDs of guests associated with this invite. Defaults
            to an empty list.
    """

    guest_ids: list[int] = Field(default_factory=list)


class InviteUpdate(BaseModel):
    """Partial data for updating an existing invite record.

    All fields are optional so a caller can update only the fields that
    actually changed; fields left unset are ignored by the service layer.

    Attributes:
        guest_ids (list[int] | None): Updated list of guest IDs, if provided.
        clear_guests (bool | None): If True, clears the invite's guest list. If
            False or None, leaves it unchanged.
        housing_needs (str | None): Updated housing needs, if provided..
        clear_housing_needs (bool | None): If True, clears the invite's housing
            needs. If False or None, leaves them unchanged.
    """

    model_config = ConfigDict(from_attributes=True)

    guest_ids: list[int] | None = None
    clear_guests: bool | None = None
    housing_needs: str | None = Field(default=None, max_length=500)
    clear_housing_needs: bool | None = None


class InviteRead(InviteBase):
    """An invite record as read back from the database.

    Attributes:
        id (int): The invite's unique ID number.
        guests (list[GuestRead]): Guests associated with this invite.
        created_at (datetime): When the invite record was created.
        updated_at (datetime): When the invite record was last updated.
    """

    id: int
    guests: list[GuestRead]
    created_at: datetime
    updated_at: datetime
