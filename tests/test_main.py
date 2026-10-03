"""Unit tests for the main module."""

import unittest

from api.extensions import limiter
from core.config import FaqEntry
from main import app


class TestAdminPages(unittest.TestCase):
    """Test cases for the admin blueprint's routes and auth guard."""

    def setUp(self):
        """Build a Flask app and test client for each test, with a known admin password."""
        self.client = app.test_client()
        limiter.reset()
        self.config = app.config["CONFIG"]
        self._original_admin_password = self.config.admin_password
        self.config.admin_password = "correct-horse-battery-staple"
        self._original_secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = app.config["SECRET_KEY"] or "test-secret-key"

    def tearDown(self):
        """Restore the original admin password and secret key configuration."""
        self.config.admin_password = self._original_admin_password
        app.config["SECRET_KEY"] = self._original_secret_key

    def test_admin_home_redirects_to_login_when_unauthenticated(self):
        """Test that GET /admin/ redirects to the login page when not logged in."""
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login", response.location)

    def test_login_page_renders_successfully(self):
        """Test that GET /admin/login renders the login form."""
        response = self.client.get("/admin/login")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/api/v1/auth/login", response.data)

    def test_login_page_does_not_handle_authentication_posts(self):
        """Test that POST /admin/login is no longer the authentication endpoint."""
        response = self.client.post("/admin/login", data={"password": "wrong"})

        self.assertEqual(response.status_code, 405)

    def test_api_login_with_correct_password_authenticates_admin_home(self):
        """Test that the API login endpoint authenticates access to /admin/."""
        response = self.client.post("/api/v1/auth/login", json={"password": "correct-horse-battery-staple"})

        self.assertEqual(response.status_code, 200)

        with self.client.session_transaction() as session:
            self.assertTrue(session.get("is_admin"))

    def test_admin_home_renders_when_authenticated(self):
        """Test that GET /admin/ renders the dummy admin page once logged in."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"/api/v1/auth/logout", response.data)

    def test_admin_home_renders_the_guest_list_section(self):
        """Test that the admin page renders the guest section with its list sub-section."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        body = self.client.get("/admin/").get_data(as_text=True)

        self.assertIn('id="admin-guests"', body)
        self.assertIn("Gästlista", body)
        self.assertIn('id="admin-guests-list"', body)
        self.assertIn("Lista alla gäster", body)

    def test_admin_home_renders_actions_from_the_registry(self):
        """Test that each action renders as a data-driven form wired to its endpoint."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        body = self.client.get("/admin/").get_data(as_text=True)

        self.assertEqual(body.count("data-admin-action"), 10)
        self.assertIn('data-method="GET"', body)
        self.assertIn('data-method="POST"', body)
        self.assertIn('data-method="PUT"', body)
        self.assertIn('data-method="DELETE"', body)
        self.assertIn('data-url-template="/api/v1/guests"', body)
        self.assertIn('data-url-template="/api/v1/guests/{guest_id}"', body)
        self.assertIn('data-url-template="/api/v1/invites"', body)
        self.assertIn('data-url-template="/api/v1/invites/{invite_id}"', body)

    def test_admin_home_loads_the_admin_script(self):
        """Test that the admin page loads the external admin.js runner with its config."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        body = self.client.get("/admin/").get_data(as_text=True)

        self.assertIn("/static/js/admin.js", body)
        self.assertIn('data-login-url="/admin/login"', body)
        self.assertIn('data-logout-url="/api/v1/auth/logout"', body)

    def test_api_logout_clears_session_and_relocks_admin_home(self):
        """Test that the API logout endpoint clears the admin session."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        logout_response = self.client.post("/api/v1/auth/logout", json={})
        self.assertEqual(logout_response.status_code, 200)

        home_response = self.client.get("/admin/")
        self.assertEqual(home_response.status_code, 302)
        self.assertIn("/admin/login", home_response.location)


class TestHomePage(unittest.TestCase):
    """Test cases for the home page."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()
        self.config = app.config["CONFIG"]
        self._original_faq = self.config.faq
        self.config.faq = [
            FaqEntry(question="Test question one?", answer="Test answer one."),
            FaqEntry(question="Test question two?", answer="Test answer two."),
        ]

    def tearDown(self):
        """Restore the original FAQ configuration."""
        self.config.faq = self._original_faq

    def test_home_page_renders_successfully(self):
        """Test that GET / renders the home page successfully."""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_home_page_with_slash_home_renders_successfully(self):
        """Test that GET /home renders the home page successfully."""
        response = self.client.get("/home")

        self.assertEqual(response.status_code, 200)

    def test_home_page_renders_configured_faq_entries(self):
        """Test that every configured FAQ question and answer is rendered on the home page."""
        body = self.client.get("/").get_data(as_text=True)

        self.assertIn("Vanliga frågor", body)
        for entry in self.config.faq:
            with self.subTest(question=entry.question):
                self.assertIn(entry.question, body)
                self.assertIn(entry.answer, body)

    def test_home_page_faq_uses_bootstrap_5_collapse_attributes(self):
        """Test that the FAQ accordion uses Bootstrap 5 data attributes so the toggle works."""
        body = self.client.get("/").get_data(as_text=True)

        self.assertIn('data-bs-toggle="collapse"', body)
        self.assertIn('data-bs-target="#faq-collapse-1"', body)
        self.assertIn('data-bs-parent="#faqSection"', body)

    def test_home_page_omits_faq_section_when_not_configured(self):
        """Test that the FAQ section is left out entirely when no entries are configured."""
        self.config.faq = []

        body = self.client.get("/").get_data(as_text=True)

        self.assertNotIn("Vanliga frågor", body)
        self.assertNotIn("faqSection", body)

    def test_unsupported_method_on_a_non_api_route_returns_html_405(self):
        """Test that a 405 outside /api/ falls back to Flask's default HTML error page."""
        response = self.client.post("/home")

        self.assertEqual(response.status_code, 405)
        self.assertIn(b"text/html", response.headers.get("Content-Type", "").encode())


class TestRsvpPage(unittest.TestCase):
    """Test cases for the rsvp blueprint's routes."""

    def setUp(self):
        """Build a Flask app and test client for each test, with a known secret key."""
        self.client = app.test_client()
        self._original_secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = app.config["SECRET_KEY"] or "test-secret-key"

    def tearDown(self):
        """Restore the original secret key configuration."""
        app.config["SECRET_KEY"] = self._original_secret_key

    def _authenticate(self, guest_id: str) -> None:
        """Establish an authenticated guest session for the given guest_id, as the search page would."""
        with self.client.session_transaction() as sess:
            sess["rsvp_guest_id"] = guest_id

    def test_rsvp_search_page_is_registered_under_rsvp_prefix(self):
        """Test that 'rsvp' page is wired to the rsvp blueprint's search page."""
        for endpoint in ["/rsvp/", "/rsvp"]:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)

    def test_rsvp_guest_page_is_registered_under_rsvp_prefix(self):
        """Test that GET /rsvp/<int:guest_id> is wired to the rsvp blueprint's guest page."""
        self._authenticate("123456")

        response = self.client.get("/rsvp/123456")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex Andersson", response.data)

    def test_post_with_valid_guest_id_redirects_to_guest_page(self):
        """Test that POSTing a valid guest_id redirects to /rsvp/<guest_id>."""
        response = self.client.post("/rsvp/", data={"guest_id": "123456"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp/123456"))

    def test_post_with_missing_guest_id_shows_inline_error(self):
        """Test that POSTing without guest_id shows an actionable inline error."""
        response = self.client.post("/rsvp/", data={})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"sexsiffriga ID-numret", response.data)

    def test_post_with_non_numeric_guest_id_shows_inline_error(self):
        """Test that POSTing a non-numeric guest_id shows an actionable inline error."""
        response = self.client.post("/rsvp/", data={"guest_id": "not-a-number"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"sexsiffriga ID-numret", response.data)

    def test_post_with_unknown_guest_id_shows_inline_error(self):
        """Test that POSTing a well-formed but unknown guest_id shows an actionable inline error."""
        response = self.client.post("/rsvp/", data={"guest_id": "999999"})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Vi hittar ingen inbjudan", response.data)

    def test_get_guest_page_renders_successfully(self):
        """Test that GET /rsvp/<int:guest_id> renders the guest's RSVP page once authenticated."""
        self._authenticate("123456")

        response = self.client.get("/rsvp/123456")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex Andersson", response.data)

    def test_get_guest_page_without_a_session_redirects_to_search(self):
        """Test that the guest_id in the URL alone cannot be used to view another guest's page."""
        response = self.client.get("/rsvp/123456")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp"))

    def test_get_guest_page_with_a_session_for_a_different_guest_redirects_to_search(self):
        """Test that a session authenticated for one guest_id cannot view a different guest's page."""
        self._authenticate("654321")

        response = self.client.get("/rsvp/123456")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp"))

    def test_guest_rsvp_can_be_saved(self):
        """Test that an authenticated guest can submit an attendance and dietary response with a valid CSRF token."""
        self._authenticate("123456")
        with self.client.session_transaction() as sess:
            csrf_token = sess.setdefault("rsvp_csrf_token", "test-csrf-token")

        response = self.client.post(
            "/rsvp/123456",
            data={
                "csrf_token": csrf_token,
                "attending": "yes",
                "bringing_plus_one": "no",
                "dietary_requirements": "Vegetarisk",
                "housing_needs": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Ditt svar", response.data)

    def test_guest_rsvp_post_without_a_session_redirects_to_search(self):
        """Test that POSTing to a guest_id without an authenticated session does not save anything."""
        response = self.client.post("/rsvp/123456", data={"attending": "yes"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/rsvp"))

    def test_guest_rsvp_post_with_an_invalid_csrf_token_is_rejected(self):
        """Test that POSTing with a missing or incorrect CSRF token shows an error and does not save."""
        self._authenticate("123456")
        with self.client.session_transaction() as sess:
            sess["rsvp_csrf_token"] = "the-real-token"

        response = self.client.post(
            "/rsvp/123456",
            data={
                "csrf_token": "a-different-token",
                "attending": "yes",
                "bringing_plus_one": "no",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sessionen har g\xc3\xa5tt ut", response.data)

    def test_unknown_guest_id_returns_a_clear_error(self):
        """Test that an authenticated but nonexistent guest ID returns a clear 404, not another guest's data."""
        self._authenticate("999999")

        response = self.client.get("/rsvp/999999")

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Vi hittar ingen inbjudan", response.data)


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

    def test_contact_page_groups_direct_contact_actions(self):
        """Test that contact details are presented as clearly labelled email and phone links."""
        body = self.client.get("/contact/").get_data(as_text=True)

        self.assertIn('class="wed-contact-card"', body)
        self.assertIn("mailto:", body)
        self.assertIn("tel:", body)
        self.assertIn("Kontakta oss", body)


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


class TestHealthCheckEndpoint(unittest.TestCase):
    """Test cases for the health check endpoint."""

    def setUp(self):
        """Build a Flask app and test client for each test."""
        self.client = app.test_client()

    def test_health_check_endpoint_returns_healthy_status(self):
        """Test that GET /api/v1/health returns a healthy status and HTTP 200."""
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"status": "healthy"})


if __name__ == "__main__":
    unittest.main()
