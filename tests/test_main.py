"""Unit tests for the main module."""

import unittest
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from api.extensions import limiter
from core.config import FaqEntry
from db.schemas import Guest, Invite, SessionLocal
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

    def test_robots_txt_is_served_from_the_site_root(self):
        """Test that crawler policy is available at /robots.txt as plain text."""
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.mimetype.startswith("text/plain"))
        self.assertEqual(response.get_data(as_text=True), "User-agent: *\nDisallow: /\n")

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

    UNKNOWN_INVITE_ID = "00000000-0000-4000-8000-000000000000"

    def setUp(self):
        """Build a test client with a known secret key, and seed a fake two-guest invite and an empty invite."""
        self.client = app.test_client()
        limiter.reset()
        self._original_secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = app.config["SECRET_KEY"] or "test-secret-key"

        db = SessionLocal()
        try:
            db.query(Guest).delete()
            db.query(Invite).delete()
            alex = Guest(name="Alex Example", plus_one_allowed=True)
            robin = Guest(name="Robin Example")
            invite = Invite(guests=[alex, robin])
            empty_invite = Invite()
            db.add_all([invite, empty_invite])
            db.commit()
            self.invite_id = invite.id
            self.empty_invite_id = empty_invite.id
            self.alex_id = alex.id
            self.robin_id = robin.id
        finally:
            db.close()

    def tearDown(self):
        """Restore the original secret key configuration."""
        app.config["SECRET_KEY"] = self._original_secret_key

    def _open_invite(self, invite_id: str) -> str:
        """Open an invite's RSVP link, as a guest scanning the QR code would, and return the session's CSRF token."""
        self.client.get(f"/rsvp/{invite_id}")
        with self.client.session_transaction() as sess:
            return sess["rsvp_csrf_token"]

    def _get_guest(self, guest_id: int) -> Guest:
        """Read a guest's current database row."""
        db = SessionLocal()
        try:
            guest = db.get(Guest, guest_id)
            assert guest is not None
            return guest
        finally:
            db.close()

    def test_rsvp_search_page_is_registered_under_rsvp_prefix(self):
        """Test that 'rsvp' page is wired to the rsvp blueprint's lookup page."""
        for endpoint in ["/rsvp/", "/rsvp"]:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                self.assertEqual(response.status_code, 200)
                self.assertIn(b'name="invite_id"', response.data)

    def test_post_with_valid_invite_id_redirects_to_invite_page(self):
        """Test that POSTing a known invite UUID, or a whole RSVP link, redirects to /rsvp/<invite_id>."""
        for code in [self.invite_id, f" {self.invite_id.upper()} ", f"https://example.com/rsvp/{self.invite_id}/"]:
            with self.subTest(code=code):
                response = self.client.post("/rsvp/", data={"invite_id": code})

                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.location.endswith(f"/rsvp/{self.invite_id}"))

    def test_post_with_missing_or_malformed_invite_id_shows_inline_error(self):
        """Test that POSTing a missing or non-UUID invite code shows an actionable inline error."""
        for data in [{}, {"invite_id": "123456"}]:
            with self.subTest(data=data):
                response = self.client.post("/rsvp/", data=data)

                self.assertEqual(response.status_code, 200)
                self.assertIn("Ange koden från din inbjudan".encode(), response.data)

    def test_post_with_unknown_invite_id_shows_inline_error(self):
        """Test that POSTing a well-formed but unknown invite UUID shows an actionable inline error."""
        response = self.client.post("/rsvp/", data={"invite_id": self.UNKNOWN_INVITE_ID})

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Vi hittar ingen inbjudan", response.data)

    def test_lookup_posts_are_rate_limited(self):
        """Test that repeated invite-code lookups are rate limited."""
        statuses = [self.client.post("/rsvp/", data={"invite_id": "x"}).status_code for _ in range(11)]

        self.assertEqual(statuses[-1], 429)

    def test_invite_link_renders_every_guest_and_authenticates_the_session(self):
        """Test that GET /rsvp/<invite_id> renders a form section for every guest and authenticates the session."""
        response = self.client.get(f"/rsvp/{self.invite_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Alex Example", response.data)
        self.assertIn(b"Robin Example", response.data)
        self.assertIn(f'name="guest-{self.alex_id}-plus_one_name"'.encode(), response.data)
        self.assertNotIn(f'name="guest-{self.robin_id}-plus_one_name"'.encode(), response.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["rsvp_invite_id"], self.invite_id)

    def test_unknown_invite_returns_a_clear_404(self):
        """Test that an unknown or non-UUID invite link returns a clear 404."""
        for path in [f"/rsvp/{self.UNKNOWN_INVITE_ID}", "/rsvp/123456"]:
            with self.subTest(path=path):
                response = self.client.get(path)

                self.assertEqual(response.status_code, 404)

        self.assertIn(b"Vi hittar ingen inbjudan", self.client.get(f"/rsvp/{self.UNKNOWN_INVITE_ID}").data)

    def test_invite_without_guests_shows_contact_message_and_no_form(self):
        """Test that an invite with no guests shows a contact message instead of the form."""
        response = self.client.get(f"/rsvp/{self.empty_invite_id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("saknar gäster".encode(), response.data)
        self.assertNotIn(b'name="csrf_token"', response.data)

    def test_invite_rsvp_can_be_saved(self):
        """Test that an authenticated session can save every guest's answers with a valid CSRF token."""
        csrf_token = self._open_invite(self.invite_id)

        response = self.client.post(
            f"/rsvp/{self.invite_id}",
            data={
                "csrf_token": csrf_token,
                f"guest-{self.alex_id}-attending": "yes",
                f"guest-{self.alex_id}-food_preferences": "Vegetarisk",
                f"guest-{self.robin_id}-attending": "no",
                "housing_needs": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Ert svar är sparat".encode(), response.data)
        self.assertTrue(self._get_guest(self.alex_id).attending)
        self.assertEqual(self._get_guest(self.alex_id).food_preferences, "Vegetarisk")
        self.assertFalse(self._get_guest(self.robin_id).attending)

    def test_invalid_answers_show_an_error_and_save_nothing(self):
        """Test that an invalid answer re-renders the form with an error and saves nothing."""
        csrf_token = self._open_invite(self.invite_id)

        response = self.client.post(
            f"/rsvp/{self.invite_id}",
            data={
                "csrf_token": csrf_token,
                f"guest-{self.alex_id}-attending": "yes",
                f"guest-{self.robin_id}-email": "not-an-email",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"giltig e-postadress", response.data)
        self.assertIsNone(self._get_guest(self.alex_id).attending)

    def test_post_without_an_authenticated_session_redirects_and_saves_nothing(self):
        """Test that POSTing without having opened this invite's link redirects back to it without saving."""
        self._open_invite(self.empty_invite_id)

        response = self.client.post(f"/rsvp/{self.invite_id}", data={f"guest-{self.alex_id}-attending": "yes"})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith(f"/rsvp/{self.invite_id}"))
        self.assertIsNone(self._get_guest(self.alex_id).attending)

    def test_post_with_an_invalid_csrf_token_is_rejected(self):
        """Test that POSTing with a missing or incorrect CSRF token shows an error and does not save."""
        self._open_invite(self.invite_id)

        response = self.client.post(
            f"/rsvp/{self.invite_id}",
            data={"csrf_token": "a-different-token", f"guest-{self.alex_id}-attending": "yes"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Sessionen har gått ut".encode(), response.data)
        self.assertIsNone(self._get_guest(self.alex_id).attending)

    def test_database_error_while_saving_returns_a_clear_500(self):
        """Test that a database failure while saving shows a friendly error with a 500 status."""
        csrf_token = self._open_invite(self.invite_id)

        with patch("services.rsvp_service.RsvpService.save_rsvp", side_effect=SQLAlchemyError("boom")):
            response = self.client.post(f"/rsvp/{self.invite_id}", data={"csrf_token": csrf_token})

        self.assertEqual(response.status_code, 500)
        self.assertIn("Något gick fel".encode(), response.data)


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
