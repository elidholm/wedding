"""Unit tests for the api.v1.health module."""

import unittest

from api.extensions import limiter
from main import app


class HealthcheckApiTestCase(unittest.TestCase):
    """Base test case giving each test a test client."""

    def setUp(self):
        """Build a fresh test client."""
        self.client = app.test_client()
        limiter.reset()


class TestListGuests(HealthcheckApiTestCase):
    """Test cases for GET /api/v1/health."""

    def test_returns_status_healthy(self):
        """Test that the healthcheck endpoint returns a 200 and the expected JSON."""
        response = self.client.get("/api/v1/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "healthy"})


class TestMethodNotAllowed(HealthcheckApiTestCase):
    """Test cases for unsupported HTTP methods on healthcheck endpoint."""

    def test_unsupported_method_returns_json_405(self):
        """Test that an unsupported method on the healthcheck endpoint returns a JSON 405."""
        response = self.client.patch("/api/v1/health")

        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.get_json())


class TestRateLimit(HealthcheckApiTestCase):
    """Test cases for rate limiting on healthcheck endpoint."""

    def test_rate_limit_exceeded_returns_json_429(self):
        """Test that exceeding the rate limit returns a JSON 429."""
        for _ in range(10):
            self.client.get("/api/v1/health")

        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 429)


if __name__ == "__main__":
    unittest.main()
