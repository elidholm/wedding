"""Unit tests for the db.schemas module."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.schemas import Base, Guest, SessionLocal, engine


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
            "plus_one",
            "allergies",
            "food_preferences",
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

    def test_create_all_creates_the_guests_table(self):
        """Test that create_all() creates the guests table on a fresh in-memory engine."""
        test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)

        table_names = test_engine.dialect.get_table_names(test_engine.connect())

        self.assertIn("guests", table_names)

    def test_a_row_can_be_inserted_and_queried_after_create_all(self):
        """Test that a Guest row can be persisted and read back after create_all()."""
        test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=test_engine)
        session = sessionmaker(bind=test_engine)()

        try:
            session.add(Guest(name="Jane Doe", plus_one=True, allergies="peanuts"))
            session.commit()

            guest = session.query(Guest).filter_by(name="Jane Doe").one()

            self.assertIsNotNone(guest.id)
            self.assertEqual(guest.name, "Jane Doe")
            self.assertIsNone(guest.email)
            self.assertIsNone(guest.attending)
            self.assertTrue(guest.plus_one)
            self.assertEqual(guest.allergies, "peanuts")
            self.assertIsNone(guest.food_preferences)

        finally:
            session.close()


if __name__ == "__main__":
    unittest.main()
