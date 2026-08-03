"""Unit tests for the main module."""

import unittest

from core.config import config
from main import app


class TestCreateApp(unittest.TestCase):
    """Test cases for the create_app application factory."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_create_app_sets_config_values(self):
        """Test that create_app copies Config fields into app.config."""
        self.assertEqual(app.config["APP_NAME"], config.app_name)
        self.assertEqual(app.config["HOST"], config.host)
        self.assertEqual(app.config["PORT"], config.port)
        self.assertEqual(app.config["DEBUG"], config.debug)


class TestHomeRoute(unittest.TestCase):
    """Test cases for the home route."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_home_route_renders_successfully(self):
        """Test that GET / renders the home page successfully."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_home_route_with_slash_home_renders_successfully(self):
        """Test that GET /home renders the home page successfully."""
        response = self.client.get("/home")

        self.assertEqual(response.status_code, 200)


class TestRsvpRoute(unittest.TestCase):
    """Test cases for the rsvp blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_rsvp_search_page_is_registered_under_rsvp_prefix(self):
        """Test that GET /rsvp/ is wired to the rsvp blueprint's search page."""
        response = self.client.get("/rsvp/")

        self.assertEqual(response.status_code, 200)

    def test_rsvp_guest_page_is_registered_under_rsvp_prefix(self):
        """Test that GET /rsvp/<int:guest_id> is wired to the rsvp blueprint's guest page."""
        response = self.client.get("/rsvp/42")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"42", response.data)

    def test_post_with_valid_guest_id_redirects_to_guest_page(self):
        """Test that POSTing a valid guest_id redirects to /rsvp/<guest_id>."""
        response = self.client.post("/rsvp/", data={"guest_id": "42"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp/42"))

    def test_post_with_missing_guest_id_redirects_back_to_search(self):
        """Test that POSTing without guest_id redirects back to the search page."""
        response = self.client.post("/rsvp/", data={})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp/"))

    def test_post_with_non_numeric_guest_id_redirects_back_to_search(self):
        """Test that POSTing a non-numeric guest_id redirects back to the search page."""
        response = self.client.post("/rsvp/", data={"guest_id": "not-a-number"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp/"))

    def test_get_guest_page_renders_successfully(self):
        """Test that GET /rsvp/<int:guest_id> renders the guest's RSVP page."""
        response = self.client.get("/rsvp/42")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"42", response.data)


class TestContactRoute(unittest.TestCase):
    """Test cases for the contact blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_contact_page_redirects_successfully(self):
        """Test that GET /contact redirects the contact page successfully."""
        response = self.client.get("/contact")

        self.assertEqual(response.status_code, 308)


class TestItineraryRoute(unittest.TestCase):
    """Test cases for the itinerary blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_itinerary_page_redirects_successfully(self):
        """Test that GET /itinerary redirects the itinerary page successfully."""
        response = self.client.get("/itinerary")

        self.assertEqual(response.status_code, 308)


class TestSeatingRoute(unittest.TestCase):
    """Test cases for the seating blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_seating_page_redirects_successfully(self):
        """Test that GET /seating redirects the seating page successfully."""
        response = self.client.get("/seating")

        self.assertEqual(response.status_code, 308)


class TestTableInfoRoute(unittest.TestCase):
    """Test cases for the table_info blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_table_info_page_renders_successfully(self):
        """Test that GET /tables renders the table info page successfully."""
        response = self.client.get("/tables/table_name")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"table_name", response.data)

    def test_table_info_page_with_missing_table_name_returns_404(self):
        """Test that GET /tables/ without a table_name returns a 404."""
        response = self.client.get("/tables/")

        self.assertEqual(response.status_code, 404)

    def test_table_info_page_with_special_characters_in_table_name_renders_successfully(
        self,
    ):
        """Test that GET /tables/<table_name> with special characters renders successfully."""
        response = self.client.get("/tables/table%20name%20with%20spaces")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"table name with spaces", response.data)

    def test_table_info_page_with_numeric_table_name_renders_successfully(self):
        """Test that GET /tables/<table_name> with a numeric table name renders successfully."""
        response = self.client.get("/tables/12345")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"12345", response.data)


if __name__ == "__main__":
    unittest.main()
