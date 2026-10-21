"""Unit tests for the db.session module."""

import unittest
from unittest.mock import patch

from flask import Flask

from db.session import get_db_session, init_app


class TestDbSession(unittest.TestCase):
    """Test cases for the request-scoped database session helpers."""

    def setUp(self):
        """Build a bare Flask app with the session teardown registered."""
        self.app = Flask(__name__)
        init_app(self.app)

    def test_reuses_one_session_per_app_context(self):
        """Test that repeated calls within one app context return the same session."""
        with self.app.app_context():
            self.assertIs(get_db_session(), get_db_session())

    def test_closes_session_on_teardown(self):
        """Test that the session is closed, without a rollback, when the context ends cleanly."""
        with patch("db.session.SessionLocal") as session_factory, self.app.app_context():
            get_db_session()

        session_factory.return_value.close.assert_called_once()
        session_factory.return_value.rollback.assert_not_called()

    def test_rolls_back_session_on_error(self):
        """Test that the session is rolled back before closing when the context ends with an error."""
        with (
            patch("db.session.SessionLocal") as session_factory,
            self.assertRaises(RuntimeError),
            self.app.app_context(),
        ):
            get_db_session()
            raise RuntimeError("boom")

        session_factory.return_value.rollback.assert_called_once()
        session_factory.return_value.close.assert_called_once()
