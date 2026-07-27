"""Unit tests for the web_server module."""

import unittest

from config import AppConfig
from web_server import create_app


class TestCreateApp(unittest.TestCase):
    """Test cases for the create_app application factory."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.app_config = AppConfig()
        self.app = create_app(self.app_config)
        self.client = self.app.test_client()

    def test_create_app_sets_config_values(self):
        """Test that create_app copies AppConfig fields into app.config."""
        self.assertEqual(self.app.config["APP_NAME"], self.app_config.app_name)
        self.assertEqual(self.app.config["HOST"], self.app_config.host)
        self.assertEqual(self.app.config["PORT"], self.app_config.port)
        self.assertEqual(self.app.config["DEBUG"], self.app_config.debug)

    def test_home_route_returns_200(self):
        """Test that the / route responds successfully."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_rsvp_route_is_permanent_redirect(self):
        """Test that the /rsvp route responds with a permanent redirect."""
        response = self.client.get("/rsvp")
        self.assertEqual(response.status_code, 308)


if __name__ == "__main__":
    unittest.main()
