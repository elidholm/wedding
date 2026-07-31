"""Unit tests for the core.config module."""

import unittest

from core.config import Config, config


class TestConfigClass(unittest.TestCase):
    """Test cases for the Config class."""

    def setUp(self):
        self.config = Config()

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


class TestConfigSingleton(unittest.TestCase):
    """Test cases for the singleton config instance."""

    def test_singleton_instance(self):
        """Test that the config instance is of type Config."""
        self.assertIsInstance(config, Config)


if __name__ == "__main__":
    unittest.main()
