"""Unit tests for the models.invite module."""

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from models.invite import InviteCreate, InviteRead, InviteUpdate


class TestInviteCreate(unittest.TestCase):
    """Test cases for the InviteCreate model."""

    def test_defaults_to_no_guests_and_no_housing_needs(self):
        """Test that an invite can be created without optional data."""
        invite = InviteCreate()

        self.assertEqual(invite.guest_ids, [])
        self.assertIsNone(invite.housing_needs)

    def test_accepts_guest_ids_and_housing_needs(self):
        """Test that invite guest IDs and housing needs are accepted."""
        invite = InviteCreate(guest_ids=[1, 2], housing_needs="Accessible room")

        self.assertEqual(invite.guest_ids, [1, 2])
        self.assertEqual(invite.housing_needs, "Accessible room")

    def test_guest_lists_are_independent_between_instances(self):
        """Test that default guest lists are not shared between invites."""
        first = InviteCreate()
        second = InviteCreate()

        first.guest_ids.append(1)

        self.assertEqual(first.guest_ids, [1])
        self.assertEqual(second.guest_ids, [])

    def test_rejects_housing_needs_over_the_length_limit(self):
        """Test that housing needs are limited to 500 characters."""
        with self.assertRaises(ValidationError):
            InviteCreate(housing_needs="x" * 501)


class TestInviteUpdate(unittest.TestCase):
    """Test cases for the InviteUpdate model."""

    def test_all_fields_are_optional(self):
        """Test that InviteUpdate can be constructed without any changes."""
        update = InviteUpdate()

        self.assertIsNone(update.guest_ids)
        self.assertIsNone(update.housing_needs)
        self.assertEqual(update.model_dump(exclude_unset=True), {})

    def test_exclude_unset_preserves_supplied_fields(self):
        """Test that explicitly supplied update values appear in exclude_unset dumps."""
        update = InviteUpdate(guest_ids=[], housing_needs=None)

        self.assertEqual(update.model_dump(exclude_unset=True), {"guest_ids": [], "housing_needs": None})

    def test_rejects_housing_needs_over_the_length_limit(self):
        """Test that updated housing needs are limited to 500 characters."""
        with self.assertRaises(ValidationError):
            InviteUpdate(housing_needs="x" * 501)


class TestInviteRead(unittest.TestCase):
    """Test cases for the InviteRead model."""

    def test_reads_invite_and_nested_guests_from_orm_attributes(self):
        """Test that InviteRead validates ORM-style attributes, including nested guest records."""
        now = datetime.now(UTC)

        class FakeGuest:
            id = 1
            name = "Jane Doe"
            email = "jane@example.com"
            attending = True
            plus_one_allowed = True
            plus_one_name = "Alex Doe"
            food_preferences = "vegan"
            created_at = now
            updated_at = now

        class FakeInvite:
            id = 4
            housing_needs = "Accessible room"
            created_at = now
            updated_at = now

            def __init__(self):
                self.guests = [FakeGuest()]

        invite = InviteRead.model_validate(FakeInvite())

        self.assertEqual(invite.id, 4)
        self.assertEqual(invite.housing_needs, "Accessible room")
        self.assertEqual(len(invite.guests), 1)
        self.assertEqual(invite.guests[0].name, "Jane Doe")
        self.assertEqual(invite.guests[0].plus_one_name, "Alex Doe")

    def test_requires_id_guests_and_timestamps(self):
        """Test that an invite read model requires persisted fields."""
        with self.assertRaises(ValidationError):
            InviteRead(housing_needs="Accessible room")


if __name__ == "__main__":
    unittest.main()
