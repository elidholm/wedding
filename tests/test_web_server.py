"""Unit tests for the web_server module."""

import unittest

from core.config import config
from web_server import create_app


class TestCreateApp(unittest.TestCase):
    """Test cases for the create_app application factory."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.app = create_app(config)
        self.client = self.app.test_client()

    def test_create_app_sets_config_values(self):
        """Test that create_app copies AppConfig fields into app.config."""
        self.assertEqual(self.app.config["APP_NAME"], config.app_name)
        self.assertEqual(self.app.config["HOST"], config.host)
        self.assertEqual(self.app.config["PORT"], config.port)
        self.assertEqual(self.app.config["DEBUG"], config.debug)


if __name__ == "__main__":
    unittest.main()
