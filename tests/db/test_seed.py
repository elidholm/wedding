"""Unit tests for the db.seed module."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schemas import Base, Guest, Invite
from db.seed import FAKE_INVITES, seed


class TestSeed(unittest.TestCase):
    """Test cases for seeding fake development invites."""

    def setUp(self):
        """Build a fresh in-memory database and session for each test."""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self):
        """Close the session opened in setUp."""
        self.session.close()

    def test_seeds_every_fake_invite_with_its_guests(self):
        """Test that every fake invite is created, at its fixed UUID, with its guests."""
        invites = seed(self.session)

        self.assertEqual([invite.id for invite in invites], list(FAKE_INVITES))
        for invite in invites:
            self.assertEqual(
                [guest.name for guest in invite.guests],
                [guest["name"] for guest in FAKE_INVITES[invite.id]],
            )

    def test_seeding_twice_creates_no_duplicates(self):
        """Test that re-running the seed leaves the database unchanged."""
        seed(self.session)
        seed(self.session)

        self.assertEqual(self.session.query(Invite).count(), len(FAKE_INVITES))
        self.assertEqual(self.session.query(Guest).count(), sum(len(guests) for guests in FAKE_INVITES.values()))
