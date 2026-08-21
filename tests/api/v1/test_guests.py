"""Unit tests for the api.v1.guests module."""

import unittest
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from db.schemas import Guest, SessionLocal
from main import app


class GuestsApiTestCase(unittest.TestCase):
    """Base test case giving each test a clean `guests` table and a test client."""

    def setUp(self):
        """Build a fresh test client and clear the shared in-memory guests table."""
        self.client = app.test_client()
        session = SessionLocal()
        try:
            session.query(Guest).delete()
            session.commit()
        finally:
            session.close()

    def _create_guest(self, **overrides):
        """Create a guest via the API and return its parsed JSON body.

        Args:
            **overrides: Fields to override on the default valid payload.

        Returns:
            dict: The created guest's JSON representation.
        """
        payload = {"name": "Jane Doe"}
        payload.update(overrides)
        response = self.client.post("/api/v1/guests", json=payload)
        assert response.status_code == 201
        return response.get_json()


class TestListGuests(GuestsApiTestCase):
    """Test cases for GET /api/v1/guests."""

    def test_returns_empty_list_when_there_are_no_guests(self):
        """Test that an empty guest table returns 200 with an empty JSON array."""
        response = self.client.get("/api/v1/guests")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_returns_every_created_guest(self):
        """Test that list_guests returns every previously created guest."""
        self._create_guest(name="Alice")
        self._create_guest(name="Bob")

        response = self.client.get("/api/v1/guests")

        self.assertEqual(response.status_code, 200)
        names = {guest["name"] for guest in response.get_json()}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure while listing guests returns a clean 500 JSON error."""
        with patch(
            "services.guest_service.GuestService.list_guests",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.get("/api/v1/guests")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())


class TestCreateGuest(GuestsApiTestCase):
    """Test cases for POST /api/v1/guests."""

    def test_creates_a_guest_and_returns_201_with_location_header(self):
        """Test that creating a guest returns 201, the guest body, and a Location header."""
        response = self.client.post(
            "/api/v1/guests",
            json={
                "name": "Jane Doe",
                "email": "jane@example.com",
                "attending": True,
                "plus_one": True,
                "allergies": "peanuts",
                "food_preferences": "vegan",
            },
        )

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["name"], "Jane Doe")
        self.assertEqual(body["email"], "jane@example.com")
        self.assertTrue(body["attending"])
        self.assertTrue(body["plus_one"])
        self.assertEqual(body["allergies"], "peanuts")
        self.assertEqual(body["food_preferences"], "vegan")
        self.assertIn(f"/api/v1/guests/{body['id']}", response.headers["Location"])

    def test_returns_400_when_body_is_missing(self):
        """Test that POSTing with no JSON body returns a 400 JSON error."""
        response = self.client.post("/api/v1/guests")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_returns_400_when_body_is_malformed_json(self):
        """Test that POSTing a malformed JSON body returns a 400 JSON error."""
        response = self.client.post(
            "/api/v1/guests",
            data="not valid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_returns_400_when_name_is_missing(self):
        """Test that omitting the required name field returns a 400 with validation details."""
        response = self.client.post("/api/v1/guests", json={"email": "jane@example.com"})

        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertIn("error", body)
        self.assertIn("details", body)

    def test_returns_400_for_invalid_email_format(self):
        """Test that an invalid email format returns a 400 with validation details."""
        response = self.client.post("/api/v1/guests", json={"name": "Jane Doe", "email": "not-an-email"})

        self.assertEqual(response.status_code, 400)
        self.assertIn("details", response.get_json())

    def test_returns_400_for_oversized_name(self):
        """Test that a name exceeding the max length returns a 400."""
        response = self.client.post("/api/v1/guests", json={"name": "x" * 200})

        self.assertEqual(response.status_code, 400)

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure during creation returns a clean 500 JSON error."""
        with patch(
            "services.guest_service.GuestService.create_guest",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.post("/api/v1/guests", json={"name": "Jane Doe"})

        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertIn("error", body)
        self.assertNotIn("boom", body["error"])


class TestGetGuest(GuestsApiTestCase):
    """Test cases for GET /api/v1/guests/<id>."""

    def test_returns_the_guest_when_it_exists(self):
        """Test that GET returns 200 and the matching guest's data."""
        created = self._create_guest(name="Jane Doe")

        response = self.client.get(f"/api/v1/guests/{created['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Jane Doe")

    def test_returns_404_when_the_guest_does_not_exist(self):
        """Test that GET for a nonexistent guest ID returns a 404 JSON error."""
        response = self.client.get("/api/v1/guests/999999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure while fetching a guest returns a clean 500 JSON error."""
        created = self._create_guest(name="Jane Doe")

        with patch(
            "services.guest_service.GuestService.get_guest",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.get(f"/api/v1/guests/{created['id']}")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())


class TestUpdateGuest(GuestsApiTestCase):
    """Test cases for PUT /api/v1/guests/<id>."""

    def test_updates_only_the_provided_fields(self):
        """Test that PUT only changes the fields explicitly provided."""
        created = self._create_guest(name="Jane Doe", allergies="peanuts")

        response = self.client.put(f"/api/v1/guests/{created['id']}", json={"attending": True})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["attending"])
        self.assertEqual(body["allergies"], "peanuts")

    def test_returns_404_when_the_guest_does_not_exist(self):
        """Test that PUT for a nonexistent guest ID returns a 404 JSON error."""
        response = self.client.put("/api/v1/guests/999999", json={"attending": True})

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_returns_400_when_body_is_missing(self):
        """Test that PUT with no JSON body returns a 400 JSON error."""
        created = self._create_guest()

        response = self.client.put(f"/api/v1/guests/{created['id']}")

        self.assertEqual(response.status_code, 400)

    def test_returns_400_for_invalid_email_format(self):
        """Test that an invalid email format on update returns a 400."""
        created = self._create_guest()

        response = self.client.put(f"/api/v1/guests/{created['id']}", json={"email": "not-an-email"})

        self.assertEqual(response.status_code, 400)

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure during update returns a clean 500 JSON error."""
        created = self._create_guest()

        with patch(
            "services.guest_service.GuestService.update_guest",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.put(f"/api/v1/guests/{created['id']}", json={"attending": True})

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("boom", response.get_json()["error"])


class TestDeleteGuest(GuestsApiTestCase):
    """Test cases for DELETE /api/v1/guests/<id>."""

    def test_deletes_the_guest_and_returns_204_with_no_body(self):
        """Test that DELETE returns 204 No Content with an empty body on success."""
        created = self._create_guest()

        response = self.client.delete(f"/api/v1/guests/{created['id']}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")

    def test_returns_404_when_the_guest_does_not_exist(self):
        """Test that DELETE for a nonexistent guest ID returns a 404 JSON error."""
        response = self.client.delete("/api/v1/guests/999999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure during deletion returns a clean 500 JSON error."""
        created = self._create_guest()

        with patch(
            "services.guest_service.GuestService.delete_guest",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.delete(f"/api/v1/guests/{created['id']}")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("boom", response.get_json()["error"])


class TestMethodNotAllowed(GuestsApiTestCase):
    """Test cases for unsupported HTTP methods on guests endpoints."""

    def test_unsupported_method_returns_json_405(self):
        """Test that an unsupported method on the guests collection returns a JSON 405."""
        response = self.client.patch("/api/v1/guests")

        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
