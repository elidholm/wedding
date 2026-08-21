"""Unit tests for the services.guest_service module."""

import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from db.schemas import Base
from services.guest_service import GuestService


class GuestServiceTestCase(unittest.TestCase):
    """Base test case that gives each test an isolated in-memory database and service."""

    def setUp(self):
        """Build a fresh in-memory database, session, and GuestService for each test."""
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.service = GuestService(self.session)

    def tearDown(self):
        """Close the session opened in setUp."""
        self.session.close()


class TestCreateGuest(GuestServiceTestCase):
    """Test cases for GuestService.create_guest."""

    def test_creates_and_returns_a_guest_with_an_id(self):
        """Test that create_guest persists the guest and returns it with an assigned ID."""
        guest = self.service.create_guest(name="Jane Doe", plus_one=True)

        self.assertIsNotNone(guest.id)
        self.assertEqual(guest.name, "Jane Doe")
        self.assertTrue(guest.plus_one)

    def test_created_guest_can_be_fetched_back(self):
        """Test that a guest created via create_guest can subsequently be fetched by ID."""
        created = self.service.create_guest(name="Jane Doe")

        fetched = self.service.get_guest(created.id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Jane Doe")

    def test_persists_email_attending_allergies_and_food_preferences(self):
        """Test that create_guest persists every optional field, not just name/plus_one."""
        guest = self.service.create_guest(
            name="Jane Doe",
            email="jane@example.com",
            attending=True,
            allergies="peanuts",
            food_preferences="vegan",
        )

        self.assertEqual(guest.email, "jane@example.com")
        self.assertTrue(guest.attending)
        self.assertEqual(guest.allergies, "peanuts")
        self.assertEqual(guest.food_preferences, "vegan")

    def test_rolls_back_and_reraises_on_a_database_error(self):
        """Test that a commit failure during create_guest rolls back and re-raises."""
        self.session.commit = MagicMock(side_effect=SQLAlchemyError("boom"))
        self.session.rollback = MagicMock()

        with self.assertRaises(SQLAlchemyError):
            self.service.create_guest(name="Jane Doe")

        self.session.rollback.assert_called_once()


class TestGetGuest(GuestServiceTestCase):
    """Test cases for GuestService.get_guest."""

    def test_returns_none_for_a_missing_guest(self):
        """Test that get_guest returns None when no guest with that ID exists."""
        self.assertIsNone(self.service.get_guest(999))


class TestListGuests(GuestServiceTestCase):
    """Test cases for GuestService.list_guests."""

    def test_returns_an_empty_list_when_there_are_no_guests(self):
        """Test that list_guests returns an empty list for a fresh database."""
        self.assertEqual(self.service.list_guests(), [])

    def test_returns_every_created_guest_ordered_by_id(self):
        """Test that list_guests returns all guests, ordered by ID."""
        first = self.service.create_guest(name="Alice")
        second = self.service.create_guest(name="Bob", plus_one=True)

        guests = self.service.list_guests()

        self.assertEqual([g.id for g in guests], [first.id, second.id])
        self.assertEqual([g.name for g in guests], ["Alice", "Bob"])
        self.assertEqual([g.plus_one for g in guests], [False, True])


class TestUpdateGuest(GuestServiceTestCase):
    """Test cases for GuestService.update_guest."""

    def test_returns_none_for_a_missing_guest(self):
        """Test that update_guest returns None when no guest with that ID exists."""
        self.assertIsNone(self.service.update_guest(999, email=None, attending=True))

    def test_updates_only_the_fields_that_were_set(self):
        """Test that update_guest only changes fields explicitly provided on GuestUpdate."""
        created = self.service.create_guest(name="Jane Doe", plus_one=True)

        updated = self.service.update_guest(
            created.id,
            name="Jayne D'hoe",
            email="test@email.com",
            attending=True,
            allergies="peanuts",
            food_preferences="vegan",
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.name, "Jayne D'hoe")
        self.assertEqual(updated.email, "test@email.com")
        self.assertTrue(updated.attending)
        self.assertTrue(updated.plus_one)
        self.assertEqual(updated.allergies, "peanuts")

    def test_persists_the_update(self):
        """Test that an update is actually persisted and visible on a subsequent fetch."""
        created = self.service.create_guest(name="Jane Doe")

        self.service.update_guest(created.id, allergies="peanuts")

        self.assertEqual(self.service.get_guest(created.id).allergies, "peanuts")

    def test_attending_can_be_set_to_false(self):
        """Test that update_guest can set attending to False (not just True)."""
        created = self.service.create_guest(name="Jane Doe")

        updated = self.service.update_guest(created.id, attending=False)

        self.assertIsNotNone(updated)
        self.assertIsNotNone(updated.attending)
        self.assertFalse(updated.attending)

    def test_rolls_back_and_reraises_on_a_database_error(self):
        """Test that a commit failure during update_guest rolls back and re-raises."""
        created = self.service.create_guest(name="Jane Doe")
        self.session.commit = MagicMock(side_effect=SQLAlchemyError("boom"))
        self.session.rollback = MagicMock()

        with self.assertRaises(SQLAlchemyError):
            self.service.update_guest(created.id, attending=True)

        self.session.rollback.assert_called_once()


class TestDeleteGuest(GuestServiceTestCase):
    """Test cases for GuestService.delete_guest."""

    def test_returns_false_for_a_missing_guest(self):
        """Test that delete_guest returns False when no guest with that ID exists."""
        self.assertFalse(self.service.delete_guest(999))

    def test_returns_true_and_removes_an_existing_guest(self):
        """Test that delete_guest removes the guest and returns True."""
        created = self.service.create_guest(name="Jane Doe")

        deleted = self.service.delete_guest(created.id)

        self.assertTrue(deleted)
        self.assertIsNone(self.service.get_guest(created.id))

    def test_rolls_back_and_reraises_on_a_database_error(self):
        """Test that a commit failure during delete_guest rolls back and re-raises."""
        created = self.service.create_guest(name="Jane Doe")
        self.session.commit = MagicMock(side_effect=SQLAlchemyError("boom"))
        self.session.rollback = MagicMock()

        with self.assertRaises(SQLAlchemyError):
            self.service.delete_guest(created.id)

        self.session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
