"""Unit tests for the db.schemas module."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schemas import Base, Guest, Invite, SessionLocal, engine


class TestModuleLevelObjects(unittest.TestCase):
    """Test cases for the module-level engine/session/Base objects."""

    def test_engine_is_configured_for_sqlite(self):
        """Test that the module's engine is bound to a SQLite database URL."""
        self.assertEqual(engine.url.get_backend_name(), "sqlite")

    def test_session_local_is_bound_to_the_module_engine(self):
        """Test that SessionLocal produces sessions bound to the module's engine."""
        session = SessionLocal()
        try:
            self.assertIs(session.get_bind(), engine)
        finally:
            session.close()

    def test_guest_schema_is_registered_on_base_metadata(self):
        """Test that Guest's table is registered on Base's metadata."""
        self.assertIn(Guest.__tablename__, Base.metadata.tables)

    def test_invite_schema_is_registered_on_base_metadata(self):
        """Test that Invite's table is registered on Base's metadata."""
        self.assertIn(Invite.__tablename__, Base.metadata.tables)


class TestGuestTable(unittest.TestCase):
    """Test cases for the Guest ORM table definition."""

    def test_table_name_is_guests(self):
        """Test that Guest maps to the 'guests' table."""
        self.assertEqual(Guest.__tablename__, "guests")

    def test_table_has_expected_columns(self):
        """Test that the guests table has every expected column."""
        expected_columns = {
            "id",
            "name",
            "email",
            "attending",
            "plus_one_allowed",
            "plus_one_name",
            "food_preferences",
            "invite_id",
            "created_at",
            "updated_at",
        }
        self.assertEqual(set(Guest.__table__.columns.keys()), expected_columns)

    def test_id_is_the_primary_key(self):
        """Test that the 'id' column is the table's primary key."""
        self.assertTrue(Guest.__table__.columns["id"].primary_key)

    def test_name_column_is_not_nullable(self):
        """Test that the 'name' column is required at the schema level."""
        self.assertFalse(Guest.__table__.columns["name"].nullable)


class TestCreateAllAgainstAFreshEngine(unittest.TestCase):
    """Test cases exercising Base.metadata.create_all against an isolated engine."""

    def test_create_all_creates_the_guest_and_invite_tables(self):
        """Test that create_all() creates both tables on a fresh in-memory engine."""
        test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)

        table_names = test_engine.dialect.get_table_names(test_engine.connect())

        self.assertEqual(set(table_names), {"guests", "invites"})

    def test_a_row_can_be_inserted_and_queried_after_create_all(self):
        """Test that a Guest row can be persisted and read back after create_all()."""
        test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)
        session = sessionmaker(bind=test_engine)()

        try:
            session.add(Guest(name="Jane Doe", plus_one_allowed=True, food_preferences="vegan"))
            session.commit()

            guest = session.query(Guest).filter_by(name="Jane Doe").one()

            self.assertIsNotNone(guest.id)
            self.assertEqual(guest.name, "Jane Doe")
            self.assertIsNone(guest.email)
            self.assertIsNone(guest.attending)
            self.assertTrue(guest.plus_one_allowed)
            self.assertIsNone(guest.plus_one_name)
            self.assertEqual(guest.food_preferences, "vegan")

        finally:
            session.close()

    def test_invite_and_guests_persist_with_bidirectional_relationship(self):
        """Test that an invite and its guests persist and expose their associations."""
        test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)
        session = sessionmaker(bind=test_engine)()

        try:
            invite = Invite(housing_needs="Accessible room")
            invite.guests = [Guest(name="Jane Doe"), Guest(name="John Doe")]
            session.add(invite)
            session.commit()

            fetched_invite = session.query(Invite).one()
            fetched_guests = session.query(Guest).order_by(Guest.name).all()

            self.assertEqual([guest.name for guest in fetched_invite.guests], ["Jane Doe", "John Doe"])
            self.assertEqual([guest.invite_id for guest in fetched_guests], [invite.id, invite.id])
            self.assertIs(fetched_guests[0].invite, fetched_invite)
            self.assertEqual(fetched_invite.housing_needs, "Accessible room")
        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
