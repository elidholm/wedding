"""Unit tests for the rsvp blueprint."""

import unittest

from main import app


class TestRsvp(unittest.TestCase):
    """Test cases for the rsvp blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

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


if __name__ == "__main__":
    unittest.main()
