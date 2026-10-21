"""Unit tests for the services.rsvp_service module."""

import unittest
from unittest.mock import MagicMock

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from db.schemas import Base, Guest, Invite
from services.rsvp_service import RsvpService, guest_field


class RsvpServiceTestCase(unittest.TestCase):
    """Base test case with an in-memory database holding one fake two-guest invite."""

    def setUp(self):
        """Build a fresh in-memory database, a fake invite, and an RsvpService for each test."""
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.alex = Guest(name="Alex Example", plus_one_allowed=True)
        self.robin = Guest(name="Robin Example")
        self.invite = Invite(guests=[self.alex, self.robin])
        self.session.add(self.invite)
        self.session.commit()
        self.service = RsvpService(self.session)

    def tearDown(self):
        """Close the session opened in setUp."""
        self.session.close()


class TestGetInvite(RsvpServiceTestCase):
    """Test cases for RsvpService.get_invite."""

    def test_returns_invite_with_its_guests(self):
        """Test that an existing invite is returned with its guests in ID order."""
        invite = self.service.get_invite(self.invite.id)

        self.assertIsNotNone(invite)
        self.assertEqual([guest.name for guest in invite.guests], ["Alex Example", "Robin Example"])

    def test_returns_none_for_unknown_invite(self):
        """Test that an unknown invite UUID returns None."""
        self.assertIsNone(self.service.get_invite("00000000-0000-4000-8000-000000000000"))


class TestSaveRsvp(RsvpServiceTestCase):
    """Test cases for RsvpService.save_rsvp."""

    def test_saves_every_guest_and_housing_needs(self):
        """Test that all guests' answers and the invite's housing needs are saved together."""
        invite = self.service.save_rsvp(
            self.invite.id,
            {
                guest_field(self.alex.id, "attending"): "yes",
                guest_field(self.alex.id, "bringing_plus_one"): "yes",
                guest_field(self.alex.id, "plus_one_name"): " Plus Example ",
                guest_field(self.alex.id, "food_preferences"): "Vegetarian",
                guest_field(self.alex.id, "email"): "alex@example.com",
                guest_field(self.robin.id, "attending"): "no",
                "housing_needs": "One night",
            },
        )

        self.assertTrue(self.alex.attending)
        self.assertEqual(self.alex.plus_one_name, "Plus Example")
        self.assertEqual(self.alex.food_preferences, "Vegetarian")
        self.assertEqual(self.alex.email, "alex@example.com")
        self.assertFalse(self.robin.attending)
        self.assertEqual(invite.housing_needs, "One night")

    def test_returns_none_for_unknown_invite(self):
        """Test that saving for an unknown invite returns None."""
        self.assertIsNone(self.service.save_rsvp("00000000-0000-4000-8000-000000000000", {}))

    def test_unanswered_attendance_keeps_previous_answer(self):
        """Test that a guest left unanswered keeps their previous attendance (None if never answered)."""
        self.robin.attending = False
        self.session.commit()

        self.service.save_rsvp(self.invite.id, {guest_field(self.alex.id, "attending"): "yes"})

        self.assertTrue(self.alex.attending)
        self.assertFalse(self.robin.attending)

    def test_blank_optional_fields_are_cleared(self):
        """Test that blank email, food preferences, and housing needs are stored as None."""
        self.alex.email = "old@example.com"
        self.alex.food_preferences = "Vegan"
        self.invite.housing_needs = "Old needs"
        self.session.commit()

        self.service.save_rsvp(self.invite.id, {guest_field(self.alex.id, "email"): "  "})

        self.assertIsNone(self.alex.email)
        self.assertIsNone(self.alex.food_preferences)
        self.assertIsNone(self.invite.housing_needs)

    def test_plus_one_is_cleared_when_guest_declines(self):
        """Test that a declining guest's plus-one name is cleared even if one was submitted."""
        self.service.save_rsvp(
            self.invite.id,
            {
                guest_field(self.alex.id, "attending"): "no",
                guest_field(self.alex.id, "bringing_plus_one"): "yes",
                guest_field(self.alex.id, "plus_one_name"): "Plus Example",
            },
        )

        self.assertIsNone(self.alex.plus_one_name)

    def test_plus_one_is_ignored_when_not_allowed(self):
        """Test that a plus-one submitted for a guest without plus-one permission is ignored."""
        self.service.save_rsvp(
            self.invite.id,
            {
                guest_field(self.robin.id, "attending"): "yes",
                guest_field(self.robin.id, "bringing_plus_one"): "yes",
                guest_field(self.robin.id, "plus_one_name"): "Plus Example",
            },
        )

        self.assertIsNone(self.robin.plus_one_name)

    def test_rejects_invalid_answers_without_saving_anything(self):
        """Test that one invalid answer rejects the whole submission and leaves every guest unchanged."""
        invalid_answers = {
            "attending": {guest_field(self.robin.id, "attending"): "maybe"},
            "missing plus-one name": {
                guest_field(self.alex.id, "attending"): "yes",
                guest_field(self.alex.id, "bringing_plus_one"): "yes",
            },
            "plus-one name too long": {
                guest_field(self.alex.id, "bringing_plus_one"): "yes",
                guest_field(self.alex.id, "plus_one_name"): "x" * 121,
            },
            "email": {guest_field(self.robin.id, "email"): "not-an-email"},
            "food preferences too long": {guest_field(self.robin.id, "food_preferences"): "x" * 501},
            "housing needs too long": {"housing_needs": "x" * 501},
        }
        for label, answers in invalid_answers.items():
            with self.subTest(label), self.assertRaises(ValueError):
                self.service.save_rsvp(self.invite.id, {guest_field(self.alex.id, "attending"): "yes", **answers})

        self.session.expire_all()
        self.assertIsNone(self.alex.attending)

    def test_rolls_back_and_reraises_on_database_error(self):
        """Test that a failed commit is rolled back and the error re-raised."""
        session = MagicMock()
        session.get.return_value = Invite(guests=[])
        session.commit.side_effect = SQLAlchemyError("boom")

        with self.assertRaises(SQLAlchemyError):
            RsvpService(session).save_rsvp("any-id", {})

        session.rollback.assert_called_once()
