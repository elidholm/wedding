"""Unit tests for the config module."""

import unittest

from config import AppConfig


class TestAppConfig(unittest.TestCase):
    """Test cases for the AppConfig class."""

    def setUp(self):
        self.config = AppConfig()

    def test_field_types(self):
        """Test that every field has the expected type."""
        self.assertIsInstance(self.config.app_name, str)
        self.assertIsInstance(self.config.flask_env, str)
        self.assertIsInstance(self.config.host, str)
        self.assertIsInstance(self.config.port, int)
        self.assertIsInstance(self.config.debug, bool)

    def test_debug_matches_flask_env(self):
        """Test that debug is True only when flask_env is 'development'."""
        self.assertEqual(self.config.debug, self.config.flask_env == "development")


if __name__ == "__main__":
    unittest.main()
