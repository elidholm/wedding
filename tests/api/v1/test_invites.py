"""Unit tests for the api.v1.invites module."""

import unittest
from unittest.mock import patch

from sqlalchemy.exc import SQLAlchemyError

from api.extensions import limiter
from db.schemas import Guest, Invite, SessionLocal
from main import app


class InvitesApiTestCase(unittest.TestCase):
    """Base test case giving each test clean `guests` and `invites` tables and an authenticated test client."""

    def setUp(self):
        """Build a fresh, admin-authenticated test client and clear the shared guests and invites tables."""
        self.client = app.test_client()
        limiter.reset()
        self._original_secret_key = app.config.get("SECRET_KEY")
        app.config["SECRET_KEY"] = app.config["SECRET_KEY"] or "test-secret-key"
        with self.client.session_transaction() as http_session:
            http_session["is_admin"] = True
        session = SessionLocal()
        try:
            session.query(Guest).delete()
            session.query(Invite).delete()
            session.commit()
        finally:
            session.close()

    def tearDown(self):
        """Restore the original secret key configuration."""
        app.config["SECRET_KEY"] = self._original_secret_key

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

    def _create_invite(self, **overrides):
        """Create an invite via the API and return its parsed JSON body.

        Args:
            **overrides: Fields to override on the default valid payload.

        Returns:
            dict: The created invite's JSON representation.
        """
        payload = {}
        payload.update(overrides)
        response = self.client.post("/api/v1/invites", json=payload)
        assert response.status_code == 201
        return response.get_json()


class TestIntvitesApiRequiresAdmin(InvitesApiTestCase):
    """Test cases asserting that invite data is never readable without an admin session."""

    def setUp(self):
        """Start from the authenticated base fixture, then drop the admin session."""
        super().setUp()
        with self.client.session_transaction() as http_session:
            http_session.pop("is_admin", None)

    def test_every_invites_route_returns_401_json_when_unauthenticated(self):
        """Test that each invite endpoint rejects unauthenticated callers with a 401 JSON error."""
        requests = [
            ("GET", "/api/v1/invites", None),
            ("POST", "/api/v1/invites", {"name": "Fake Guest"}),
            ("GET", "/api/v1/invites/1", None),
            ("PUT", "/api/v1/invites/1", {"attending": True}),
            ("DELETE", "/api/v1/invites/1", None),
        ]

        for method, path, payload in requests:
            with self.subTest(method=method, path=path):
                response = self.client.open(path, method=method, json=payload)

                self.assertEqual(response.status_code, 401)
                self.assertIn("error", response.get_json())

    def test_unauthenticated_list_does_not_leak_invite_data(self):
        """Test that an unauthenticated list request returns no invite fields at all."""
        with self.client.session_transaction() as http_session:
            http_session["is_admin"] = True
        guest = self._create_guest(name="Fake Guest", email="fake@example.com", food_preferences="peanut-free")
        self._create_invite(guest_ids=[guest["id"]], housing_needs="Test string")
        with self.client.session_transaction() as http_session:
            http_session.pop("is_admin", None)

        response = self.client.get("/api/v1/invites")

        self.assertEqual(response.status_code, 401)
        self.assertNotIn(b"Test string", response.data)
        self.assertNotIn(b"Fake Guest", response.data)
        self.assertNotIn(b"peanut-free", response.data)


class TestListInvites(InvitesApiTestCase):
    """Test cases for GET /api/v1/invites."""

    def test_returns_empty_list_when_there_are_no_invites(self):
        """Test that an empty invites table returns 200 with an empty JSON array."""
        response = self.client.get("/api/v1/invites")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), [])

    def test_returns_every_created_invite(self):
        """Test that list_invite returns every previously created invite."""
        alice = self._create_guest(name="Alice")
        bob = self._create_guest(name="Bob")

        self._create_invite(guest_ids=[alice["id"]], housing_needs="Alice's needs")
        self._create_invite(guest_ids=[bob["id"]], housing_needs="Bob's needs")

        response = self.client.get("/api/v1/invites")

        self.assertEqual(response.status_code, 200)
        needs = {invite["housing_needs"] for invite in response.get_json()}
        self.assertEqual(needs, {"Alice's needs", "Bob's needs"})
        names = {guest["name"] for invite in response.get_json() for guest in invite["guests"]}
        self.assertEqual(names, {"Alice", "Bob"})

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure while listing invites returns a clean 500 JSON error."""
        with patch(
            "services.invite_service.InviteService.list_invites",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.get("/api/v1/invites")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())


class TestCreateInvite(InvitesApiTestCase):
    """Test cases for POST /api/v1/invites."""

    def setUp(self):
        """Start from the authenticated base fixture, then create a guest to associate with invites."""
        super().setUp()
        self.alice = self._create_guest(name="Alice")

    def test_creates_an_invite_and_returns_201_with_location_header(self):
        """Test that creating an invite returns 201, the invite body, and a Location header."""
        response = self.client.post(
            "/api/v1/invites", json={"guest_ids": [self.alice["id"]], "housing_needs": "No need"}
        )

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body["housing_needs"], "No need")
        self.assertEqual(len(body["guests"]), 1)
        self.assertEqual(body["guests"][0]["name"], self.alice["name"])
        self.assertIn(f"/api/v1/invites/{body['id']}", response.headers["Location"])

    def test_returns_400_when_body_is_missing(self):
        """Test that POSTing with no JSON body returns a 400 JSON error."""
        response = self.client.post("/api/v1/invites")

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_returns_400_when_body_is_malformed_json(self):
        """Test that POSTing a malformed JSON body returns a 400 JSON error."""
        response = self.client.post(
            "/api/v1/invites",
            data="not valid json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_returns_400_for_oversized_housing_needs(self):
        """Test that a housing need exceeding the max length returns a 400."""
        response = self.client.post("/api/v1/invites", json={"housing_needs": "x" * 501})

        self.assertEqual(response.status_code, 400)

    def test_returns_400_for_invalid_guest_ids(self):
        """Test that a guest ID that doesn't exist returns a 400 JSON error."""
        response = self.client.post("/api/v1/invites", json={"guest_ids": [999999]})

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure during creation returns a clean 500 JSON error."""
        with patch(
            "services.invite_service.InviteService.create_invite",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.post(
                "/api/v1/invites", json={"guest_ids": [self.alice["id"]], "housing_needs": "No need"}
            )

        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertIn("error", body)
        self.assertNotIn("boom", body["error"])


class TestGetInvite(InvitesApiTestCase):
    """Test cases for GET /api/v1/invites/<id>."""

    def test_returns_the_invite_when_it_exists(self):
        """Test that GET returns 200 and the matching invite's data."""
        guest = self._create_guest(name="Jane Doe")
        created = self._create_invite(guest_ids=[guest["id"]], housing_needs="Accessible room")

        response = self.client.get(f"/api/v1/invites/{created['id']}")

        self.assertEqual(response.status_code, 200)
        invite_data = response.get_json()
        self.assertEqual(invite_data["housing_needs"], "Accessible room")
        self.assertEqual(len(invite_data["guests"]), 1)
        self.assertEqual(invite_data["guests"][0]["name"], "Jane Doe")

    def test_returns_404_when_the_invite_does_not_exist(self):
        """Test that GET for a nonexistent invite ID returns a 404 JSON error."""
        response = self.client.get("/api/v1/invites/999999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure while fetching an invite returns a clean 500 JSON error."""
        created = self._create_invite()

        with patch(
            "services.invite_service.InviteService.get_invite",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.get(f"/api/v1/invites/{created['id']}")

        self.assertEqual(response.status_code, 500)
        self.assertIn("error", response.get_json())


class TestUpdateInvite(InvitesApiTestCase):
    """Test cases for PUT /api/v1/invites/<id>."""

    def setUp(self):
        """Start from the authenticated base fixture, then create a guest to associate with invites."""
        super().setUp()
        self.alice = self._create_guest(name="Alice")
        self.bob = self._create_guest(name="Bob")

    def test_updates_only_the_provided_fields(self):
        """Test that PUT only changes the fields explicitly provided."""
        created = self._create_invite(guest_ids=[self.alice["id"]], housing_needs="Alice's needs")

        response = self.client.put(f"/api/v1/invites/{created['id']}", json={"housing_needs": "Updated needs"})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["housing_needs"], "Updated needs")
        self.assertEqual(len(body["guests"]), 1)
        self.assertEqual(body["guests"][0]["name"], self.alice["name"])

    def test_can_add_guests_to_existing_invite(self):
        """Test that PUT can add new guests to an existing invite."""
        created = self._create_invite(guest_ids=[self.alice["id"]])

        response = self.client.put(
            f"/api/v1/invites/{created['id']}", json={"guest_ids": [self.alice["id"], self.bob["id"]]}
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual({guest["name"] for guest in body["guests"]}, {"Alice", "Bob"})

    def test_clear_guests_flag_clears_existing_value(self):
        """Test that the explicit clear flag removes an existing guests."""
        created = self._create_invite(guest_ids=[self.alice["id"]])

        response = self.client.put(
            f"/api/v1/invites/{created['id']}",
            json={"clear_guests": True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["guests"], [])

    def test_clear_housing_needs_flag_clears_existing_value(self):
        """Test that the explicit clear flag removes an existing housing needs value."""
        created = self._create_invite(housing_needs="Needs something")

        response = self.client.put(
            f"/api/v1/invites/{created['id']}",
            json={"clear_housing_needs": True},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.get_json()["housing_needs"])

    def test_returns_404_when_the_invite_does_not_exist(self):
        """Test that PUT for a nonexistent invite ID returns a 404 JSON error."""
        response = self.client.put("/api/v1/invites/999999", json={"housing_needs": "Updated needs"})

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_returns_400_when_body_is_missing(self):
        """Test that PUT with no JSON body returns a 400 JSON error."""
        created = self._create_invite()

        response = self.client.put(f"/api/v1/invites/{created['id']}")

        self.assertEqual(response.status_code, 400)

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure during update returns a clean 500 JSON error."""
        created = self._create_invite()

        with patch(
            "services.invite_service.InviteService.update_invite",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.put(f"/api/v1/invites/{created['id']}", json={"housing_needs": "Updated needs"})

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("boom", response.get_json()["error"])


class TestDeleteInvite(InvitesApiTestCase):
    """Test cases for DELETE /api/v1/invites/<id>."""

    def test_deletes_the_invite_and_returns_204_with_no_body(self):
        """Test that DELETE returns 204 No Content with an empty body on success."""
        created = self._create_invite()

        response = self.client.delete(f"/api/v1/invites/{created['id']}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b"")

    def test_returns_404_when_the_invite_does_not_exist(self):
        """Test that DELETE for a nonexistent invite ID returns a 404 JSON error."""
        response = self.client.delete("/api/v1/invites/999999")

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    def test_returns_500_when_the_database_fails(self):
        """Test that a database failure during deletion returns a clean 500 JSON error."""
        created = self._create_invite()

        with patch(
            "services.invite_service.InviteService.delete_invite",
            side_effect=SQLAlchemyError("boom"),
        ):
            response = self.client.delete(f"/api/v1/invites/{created['id']}")

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("boom", response.get_json()["error"])


class TestMethodNotAllowed(InvitesApiTestCase):
    """Test cases for unsupported HTTP methods on invites endpoints."""

    def test_unsupported_method_returns_json_405(self):
        """Test that an unsupported method on the invites collection returns a JSON 405."""
        response = self.client.patch("/api/v1/invites")

        self.assertEqual(response.status_code, 405)
        self.assertIn("error", response.get_json())


class TestRateLimit(InvitesApiTestCase):
    """Test cases for rate limiting on invites endpoints."""

    def test_rate_limit_exceeded_returns_json_429(self):
        """Test that exceeding the rate limit returns a JSON 429."""
        for _ in range(30):
            self.client.get("/api/v1/invites")

        response = self.client.get("/api/v1/invites")
        self.assertEqual(response.status_code, 429)


if __name__ == "__main__":
    unittest.main()
