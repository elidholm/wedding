"""Unit tests for the main module."""

import unittest

from main import app


class TestHomePage(unittest.TestCase):
    """Test cases for the home page."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_home_page_renders_successfully(self):
        """Test that GET / renders the home page successfully."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_home_page_with_slash_home_renders_successfully(self):
        """Test that GET /home renders the home page successfully."""
        response = self.client.get("/home")

        self.assertEqual(response.status_code, 200)


class TestRsvpPage(unittest.TestCase):
    """Test cases for the rsvp blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_rsvp_search_page_is_registered_under_rsvp_prefix(self):
        """Test that 'rsvp' page is wired to the rsvp blueprint's search page."""
        for endpoint in ["/rsvp/", "/rsvp"]:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
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


class TestContactPage(unittest.TestCase):
    """Test cases for the contact blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_contact_page_renders_successfully(self):
        """Test that 'contact' page renders the contact page successfully."""
        for endpoint in ["/contact/", "/contact"]:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)


class TestItineraryPage(unittest.TestCase):
    """Test cases for the itinerary blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_itinerary_page_renders_successfully(self):
        """Test that 'itinerary' page renders the itinerary page successfully."""
        for endpoint in ["/itinerary/", "/itinerary"]:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)


class TestSeatingPage(unittest.TestCase):
    """Test cases for the seating blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_seating_page_renders_successfully(self):
        """Test that 'seating' page renders the seating page successfully."""
        for endpoint in ["/seating/", "/seating"]:
            with self.subTest(endpoint=endpoint):
                reponse = self.client.get(endpoint)
                self.assertEqual(reponse.status_code, 200)


class TestTableInfoPage(unittest.TestCase):
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
