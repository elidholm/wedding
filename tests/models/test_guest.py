"""Unit tests for the models.guest module."""

import unittest
from datetime import UTC, datetime

from pydantic import ValidationError

from models.guest import GuestCreate, GuestRead, GuestUpdate


class TestGuestCreate(unittest.TestCase):
    """Test cases for the GuestCreate model."""

    def test_name_is_required(self):
        """Test that constructing a GuestCreate without a name raises a ValidationError."""
        with self.assertRaises(ValidationError):
            GuestCreate()

    def test_defaults_are_applied(self):
        """Test that GuestCreate applies its documented defaults when only name is given."""
        guest = GuestCreate(name="Jane Doe")

        self.assertFalse(guest.plus_one)
        self.assertIsNone(guest.attending)
        self.assertIsNone(guest.email)
        self.assertIsNone(guest.allergies)
        self.assertIsNone(guest.food_preferences)

    def test_all_fields_can_be_set(self):
        """Test that every GuestCreate field can be explicitly provided."""
        guest = GuestCreate(
            name="Jane Doe",
            email="jane@example.com",
            attending=True,
            plus_one=True,
            allergies="peanuts, lactose",
            food_preferences="vegetarian",
        )

        self.assertEqual(guest.email, "jane@example.com")
        self.assertTrue(guest.attending)
        self.assertTrue(guest.plus_one)
        self.assertEqual(guest.allergies, "peanuts, lactose")
        self.assertEqual(guest.food_preferences, "vegetarian")

    def test_rejects_an_invalid_email_format(self):
        """Test that constructing a GuestCreate with a malformed email raises a ValidationError."""
        with self.assertRaises(ValidationError):
            GuestCreate(name="Jane Doe", email="not-an-email")

    def test_rejects_an_empty_name(self):
        """Test that constructing a GuestCreate with an empty name raises a ValidationError."""
        with self.assertRaises(ValidationError):
            GuestCreate(name="")

    def test_rejects_a_name_over_the_length_limit(self):
        """Test that constructing a GuestCreate with an over-long name raises a ValidationError."""
        with self.assertRaises(ValidationError):
            GuestCreate(name="x" * 121)


class TestGuestUpdate(unittest.TestCase):
    """Test cases for the GuestUpdate model."""

    def test_all_fields_are_optional(self):
        """Test that GuestUpdate can be constructed with no arguments at all."""
        update = GuestUpdate()

        self.assertIsNone(update.name)
        self.assertIsNone(update.email)
        self.assertIsNone(update.attending)
        self.assertIsNone(update.allergies)
        self.assertIsNone(update.food_preferences)

    def test_model_dump_exclude_unset_only_returns_provided_fields(self):
        """Test that exclude_unset=True only returns fields explicitly set by the caller."""
        update = GuestUpdate(attending=True, allergies="peanuts, lactose")

        self.assertEqual(update.model_dump(exclude_unset=True), {"attending": True, "allergies": "peanuts, lactose"})

    def test_rejects_an_invalid_email_format(self):
        """Test that constructing a GuestUpdate with a malformed email raises a ValidationError."""
        with self.assertRaises(ValidationError):
            GuestUpdate(email="not-an-email")

    def test_rejects_a_name_over_the_length_limit(self):
        """Test that constructing a GuestUpdate with an over-long name raises a ValidationError."""
        with self.assertRaises(ValidationError):
            GuestUpdate(name="x" * 121)


class TestGuestRead(unittest.TestCase):
    """Test cases for the GuestRead model."""

    def test_can_be_constructed_from_an_orm_like_object(self):
        """Test that GuestRead.model_validate() works against an arbitrary object with matching attributes."""

        class FakeOrmGuest:
            id = 1
            name = "Jane Doe"
            email = None
            attending = None
            plus_one = True
            allergies = None
            food_preferences = None
            created_at = datetime.now(UTC)
            updated_at = datetime.now(UTC)

        guest = GuestRead.model_validate(FakeOrmGuest())

        self.assertEqual(guest.id, 1)
        self.assertEqual(guest.name, "Jane Doe")

    def test_id_created_at_and_updated_at_are_required(self):
        """Test that GuestRead requires id, created_at, and updated_at."""
        with self.assertRaises(ValidationError):
            GuestRead(name="Jane Doe")


if __name__ == "__main__":
    unittest.main()
