"""Unit tests for the services.invite_service module."""

import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from db.schemas import Base, Guest
from services.invite_service import InvalidInviteError, InviteService


class InviteServiceTestCase(unittest.TestCase):
    """Base test case that gives each test an isolated in-memory database and service."""

    def setUp(self):
        """Build a fresh in-memory database, session, and InviteService for each test."""
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.service = InviteService(self.session)

    def tearDown(self):
        """Close the session opened in setUp."""
        self.session.close()


class TestCreateInvite(InviteServiceTestCase):
    """Test cases for InviteService.create_invite."""

    def setUp(self):
        super().setUp()

        self.test_guest_1 = Guest(name="Guest 1")
        self.test_guest_2 = Guest(name="Guest 2")
        self.test_guest_3 = Guest(name="Guest 3")
        self.session.add(self.test_guest_1)
        self.session.add(self.test_guest_2)
        self.session.add(self.test_guest_3)

    def test_creates_and_returns_a_invite_with_an_id(self):
        """Test that create_invite persists the invite and returns it with an assigned ID."""
        invite = self.service.create_invite(guest_ids=[1], housing_needs="Needs a place to stay")

        self.assertIsNotNone(invite.id)
        self.assertEqual(invite.guests, [self.test_guest_1])
        self.assertEqual(invite.housing_needs, "Needs a place to stay")

    def test_creates_with_arguments(self):
        """Test that create invite works with no arguments given."""
        invite = self.service.create_invite()

        self.assertIsNotNone(invite.id)
        self.assertEqual(invite.guests, [])
        self.assertIsNone(invite.housing_needs)

    def test_created_invite_can_be_fetched_back(self):
        """Test that a invite created via create_invite can subsequently be fetched by ID."""
        created = self.service.create_invite(guest_ids=[1, 2], housing_needs="Needs a place to stay")

        fetched = self.service.get_invite(created.id)

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.guests, [self.test_guest_1, self.test_guest_2])
        self.assertEqual(fetched.housing_needs, "Needs a place to stay")

    def test_rolls_back_and_reraises_on_a_database_error(self):
        """Test that a commit failure during create_invite rolls back and re-raises."""
        self.session.commit = MagicMock(side_effect=SQLAlchemyError("boom"))
        self.session.rollback = MagicMock()

        with self.assertRaises(SQLAlchemyError):
            self.service.create_invite()

        self.session.rollback.assert_called_once()

    def test_raises_invalid_invite_error_for_nonexistent_guest_id(self):
        """Test that create_invite raises InvalidInviteError when given a guest ID that don't exist."""
        with self.assertRaises(InvalidInviteError) as context:
            self.service.create_invite(guest_ids=[999])

        self.assertIn("Guest 999 does not exist", str(context.exception))

    def test_raises_invalid_invite_error_for_multiple_nonexistent_guest_ids(self):
        """Test that create_invite raises InvalidInviteError when given multiple guest IDs that don't exist."""
        with self.assertRaises(InvalidInviteError) as context:
            self.service.create_invite(guest_ids=[999, 1000])

        self.assertIn("Guests 999, 1000 do not exist", str(context.exception))


class TestGetInvite(InviteServiceTestCase):
    """Test cases for InviteService.get_invite."""

    def test_returns_none_for_a_missing_invite(self):
        """Test that get_invite returns None when no invite with that ID exists."""
        self.assertIsNone(self.service.get_invite(999))


class TestListInvites(InviteServiceTestCase):
    """Test cases for InviteService.list_invites."""

    def setUp(self):
        super().setUp()

        self.test_guest_1 = Guest(name="Guest 1")
        self.test_guest_2 = Guest(name="Guest 2")
        self.test_guest_3 = Guest(name="Guest 3")
        self.session.add(self.test_guest_1)
        self.session.add(self.test_guest_2)
        self.session.add(self.test_guest_3)

    def test_returns_an_empty_list_when_there_are_no_invites(self):
        """Test that list_invites returns an empty list for a fresh database."""
        self.assertEqual(self.service.list_invites(), [])

    def test_returns_every_created_invite_ordered_by_id(self):
        """Test that list_invites returns all invites, ordered by ID."""
        first = self.service.create_invite(guest_ids=[1, 2], housing_needs="test 1")
        second = self.service.create_invite(guest_ids=[3], housing_needs="test 2")

        invites = self.service.list_invites()

        self.assertEqual([g.id for g in invites], [first.id, second.id])
        self.assertEqual([g.guests for g in invites], [[self.test_guest_1, self.test_guest_2], [self.test_guest_3]])
        self.assertEqual([g.housing_needs for g in invites], ["test 1", "test 2"])


class TestUpdateInvite(InviteServiceTestCase):
    """Test cases for InviteService.update_invite."""

    def setUp(self):
        super().setUp()

        self.test_guest_1 = Guest(name="Guest 1")
        self.test_guest_2 = Guest(name="Guest 2")
        self.test_guest_3 = Guest(name="Guest 3")
        self.session.add(self.test_guest_1)
        self.session.add(self.test_guest_2)
        self.session.add(self.test_guest_3)

    def test_returns_none_for_a_missing_invite(self):
        """Test that update_invite returns None when no invite with that ID exists."""
        self.assertIsNone(self.service.update_invite(999, housing_needs="test"))

    def test_updates_only_the_fields_that_were_set(self):
        """Test that update_invite only changes fields explicitly provided on InviteUpdate."""
        created = self.service.create_invite(guest_ids=[1], housing_needs="Needs a place to stay")

        updated = self.service.update_invite(created.id, housing_needs="Updated housing needs")

        self.assertIsNotNone(updated)
        self.assertEqual(updated.guests, [self.test_guest_1])  # unchanged
        self.assertEqual(updated.housing_needs, "Updated housing needs")

    def test_persists_the_update(self):
        """Test that an update is actually persisted and visible on a subsequent fetch."""
        created = self.service.create_invite()

        self.service.update_invite(created.id, housing_needs="test")

        self.assertEqual(self.service.get_invite(created.id).housing_needs, "test")

    def test_clear_flags_remove_existing_optional_values(self):
        """Test that explicit clear flags clear guest_ids and housing_needs."""
        created = self.service.create_invite(guest_ids=[1, 2, 3], housing_needs="Needs a place to stay")

        updated = self.service.update_invite(
            created.id,
            guest_ids=[2, 3],
            clear_guests=True,
            housing_needs="Updated housing needs",
            clear_housing_needs=True,
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.guests, [])
        self.assertIsNone(updated.housing_needs)

    def test_rolls_back_and_reraises_on_a_database_error(self):
        """Test that a commit failure during update_invite rolls back and re-raises."""
        created = self.service.create_invite(guest_ids=[], housing_needs="Needs a place to stay")
        self.session.commit = MagicMock(side_effect=SQLAlchemyError("boom"))
        self.session.rollback = MagicMock()

        with self.assertRaises(SQLAlchemyError):
            self.service.update_invite(created.id, housing_needs="Updated housing needs")

        self.session.rollback.assert_called_once()

    def test_raises_invalid_invite_error_for_nonexistent_guest_id(self):
        """Test that update_invite raises InvalidInviteError when given a guest ID that don't exist."""
        created = self.service.create_invite()

        with self.assertRaises(InvalidInviteError) as context:
            self.service.update_invite(created.id, guest_ids=[999])

        self.assertIn("Guest 999 does not exist", str(context.exception))

    def test_raises_invalid_invite_error_for_multiple_nonexistent_guest_ids(self):
        """Test that update_invite raises InvalidInviteError when given multiple guest IDs that don't exist."""
        created = self.service.create_invite()

        with self.assertRaises(InvalidInviteError) as context:
            self.service.update_invite(created.id, guest_ids=[999, 1000])

        self.assertIn("Guests 999, 1000 do not exist", str(context.exception))


class TestDeleteInvite(InviteServiceTestCase):
    """Test cases for InviteService.delete_invite."""

    def test_returns_false_for_a_missing_invite(self):
        """Test that delete_invite returns False when no invite with that ID exists."""
        self.assertFalse(self.service.delete_invite(999))

    def test_returns_true_and_removes_an_existing_invite(self):
        """Test that delete_invite removes the invite and returns True."""
        created = self.service.create_invite()

        deleted = self.service.delete_invite(created.id)

        self.assertTrue(deleted)
        self.assertIsNone(self.service.get_invite(created.id))

    def test_rolls_back_and_reraises_on_a_database_error(self):
        """Test that a commit failure during delete_invite rolls back and re-raises."""
        created = self.service.create_invite()
        self.session.commit = MagicMock(side_effect=SQLAlchemyError("boom"))
        self.session.rollback = MagicMock()

        with self.assertRaises(SQLAlchemyError):
            self.service.delete_invite(created.id)

        self.session.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
