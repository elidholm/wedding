"""Unit tests for the api.v1.auth module."""

import unittest

from api.extensions import limiter
from main import app


class AuthApiTestCase(unittest.TestCase):
    """Base test case giving each test a configured admin password."""

    def setUp(self):
        """Build a fresh test client and configure admin auth."""
        self.client = app.test_client()
        limiter.reset()
        self.config = app.config["CONFIG"]
        self._original_admin_password = self.config.admin_password
        self.config.admin_password = "correct-horse-battery-staple"
        self._original_secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = app.config["SECRET_KEY"] or "test-secret-key"

    def tearDown(self):
        """Restore admin auth configuration."""
        self.config.admin_password = self._original_admin_password
        app.config["SECRET_KEY"] = self._original_secret_key


class TestLogin(AuthApiTestCase):
    """Test cases for POST /api/v1/auth/login."""

    def test_login_with_correct_password_returns_success_json_and_sets_session(self):
        """Test that valid admin credentials return JSON and authenticate the session."""
        response = self.client.post("/api/v1/auth/login", json={"password": "correct-horse-battery-staple"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"code": "login_successful", "message": "Logged in successfully."},
        )
        with self.client.session_transaction() as session:
            self.assertTrue(session.get("is_admin"))

    def test_login_with_wrong_password_returns_error_json_and_does_not_set_session(self):
        """Test that invalid credentials return 401 JSON and leave the session unauthenticated."""
        response = self.client.post("/api/v1/auth/login", json={"password": "wrong"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"code": "invalid_credentials", "message": "Incorrect password."})
        with self.client.session_transaction() as session:
            self.assertNotIn("is_admin", session)

    def test_login_with_wrong_password_clears_existing_admin_session(self):
        """Test that a failed login attempt clears any existing admin session."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        response = self.client.post("/api/v1/auth/login", json={"password": "wrong"})

        self.assertEqual(response.status_code, 401)
        with self.client.session_transaction() as session:
            self.assertNotIn("is_admin", session)

    def test_login_with_missing_json_returns_error_json(self):
        """Test that a missing JSON body returns a structured 400 response."""
        response = self.client.post("/api/v1/auth/login")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.get_json(),
            {"code": "invalid_request", "message": "Request body must be a valid JSON object."},
        )

    def test_login_with_missing_password_returns_error_json(self):
        """Test that a JSON body without a password returns a structured 400 response."""
        response = self.client.post("/api/v1/auth/login", json={})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"code": "invalid_request", "message": "Password is required."})

    def test_login_when_admin_password_is_disabled_returns_error_json(self):
        """Test that login is rejected explicitly when no admin password is configured."""
        self.config.admin_password = None

        response = self.client.post("/api/v1/auth/login", json={"password": "anything"})

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.get_json(),
            {"code": "admin_login_disabled", "message": "Admin login is not configured."},
        )


class TestLogout(AuthApiTestCase):
    """Test cases for POST /api/v1/auth/logout."""

    def test_logout_returns_success_json_and_clears_session(self):
        """Test that logout returns JSON and removes the admin session flag."""
        with self.client.session_transaction() as session:
            session["is_admin"] = True

        response = self.client.post("/api/v1/auth/logout", json={})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"code": "logout_successful", "message": "Logged out successfully."},
        )
        with self.client.session_transaction() as session:
            self.assertNotIn("is_admin", session)

    def test_logout_is_idempotent_when_already_logged_out(self):
        """Test that logout returns a success JSON response without an active admin session."""
        response = self.client.post("/api/v1/auth/logout", json={})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json(),
            {"code": "logout_successful", "message": "Logged out successfully."},
        )


class TestMethodNotAllowed(AuthApiTestCase):
    """Test cases for unsupported HTTP methods on auth endpoints."""

    def test_unsupported_method_returns_json_405(self):
        """Test that unsupported methods return JSON 405 responses."""
        response = self.client.get("/api/v1/auth/login")

        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.get_json())


class TestRateLimit(AuthApiTestCase):
    """Test cases for auth endpoint rate limiting."""

    def test_login_rate_limit_exceeded_returns_json_429(self):
        """Test that exceeding the login rate limit returns a JSON 429."""
        for _ in range(5):
            self.client.post("/api/v1/auth/login", json={"password": "wrong"})

        response = self.client.post("/api/v1/auth/login", json={"password": "wrong"})

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.get_json(), {"code": "rate_limited", "message": "Too many requests."})


if __name__ == "__main__":
    unittest.main()
