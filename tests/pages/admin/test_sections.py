"""Unit tests for the pages.admin.sections module."""

import unittest

from flask import Blueprint, Flask

from main import app
from pages.admin.sections import (
    SECTIONS,
    AdminAction,
    AdminField,
    AdminRegistryError,
    AdminSection,
    resolve_url_template,
    validate_sections,
)


def _fake_app() -> Flask:
    """Build a throwaway app with a small fake resource to validate against."""
    fake_app = Flask(__name__)
    bp = Blueprint("things", __name__)

    @bp.get("")
    def list_things() -> str:
        return "[]"

    @bp.get("/<int:thing_id>")
    def get_thing(thing_id: int) -> str:
        return "{}"

    @bp.put("/<int:thing_id>")
    def update_thing(thing_id: int) -> str:
        return "{}"

    @bp.delete("/<int:thing_id>")
    def delete_thing(thing_id: int) -> str:
        return ""

    fake_app.register_blueprint(bp, url_prefix="/api/things")
    return fake_app


def _section(*actions: AdminAction, section_id: str = "things") -> tuple[AdminSection, ...]:
    """Wrap actions in a single-section registry."""
    return (AdminSection(id=section_id, title="Things", description="Fake things.", actions=actions),)


_THING_ID = AdminField("thing_id", "Thing ID", type="integer", location="path", required=True)


class TestShippedRegistry(unittest.TestCase):
    """Test cases for the registry that actually ships in SECTIONS."""

    def test_shipped_sections_validate_against_the_real_app(self):
        """Test that every shipped section and action resolves against the real app."""
        validate_sections(app)

    def test_guest_section_lists_all_guests(self):
        """Test that the guest section ships the list-all-guests action."""
        guests = next(section for section in SECTIONS if section.id == "guests")

        endpoints = [action.endpoint for action in guests.actions]
        self.assertIn("guests.list_guests", endpoints)


class TestResolveUrlTemplate(unittest.TestCase):
    """Test cases for resolve_url_template."""

    def test_rule_without_arguments_is_returned_verbatim(self):
        """Test that a parameterless rule resolves to its plain path."""
        action = AdminAction("list", "List", "d", "guests.list_guests")

        self.assertEqual(resolve_url_template(app, action), "/api/v1/guests")

    def test_typed_rule_arguments_become_placeholders(self):
        """Test that a converter-typed argument becomes a {name} placeholder."""
        action = AdminAction("get", "Get", "d", "guests.get_guest")

        self.assertEqual(resolve_url_template(app, action), "/api/v1/guests/{guest_id}")

    def test_unknown_endpoint_raises(self):
        """Test that resolving an unknown endpoint raises AdminRegistryError."""
        action = AdminAction("x", "X", "d", "guests.nope")

        with self.assertRaises(AdminRegistryError):
            resolve_url_template(app, action)


class TestValidateSections(unittest.TestCase):
    """Test cases for validate_sections' fail-fast checks."""

    def setUp(self):
        """Build a fresh fake app for each test."""
        self.app = _fake_app()

    def test_valid_registry_with_path_and_body_fields_passes(self):
        """Test that a well-formed registry covering every method validates."""
        validate_sections(
            self.app,
            _section(
                AdminAction("list", "List", "d", "things.list_things"),
                AdminAction("get", "Get", "d", "things.get_thing", fields=(_THING_ID,)),
                AdminAction(
                    "update",
                    "Update",
                    "d",
                    "things.update_thing",
                    method="PUT",
                    fields=(_THING_ID, AdminField("name", "Name"), AdminField("active", "Active", type="tri_bool")),
                ),
                AdminAction(
                    "delete",
                    "Delete",
                    "d",
                    "things.delete_thing",
                    method="DELETE",
                    fields=(_THING_ID,),
                    destructive=True,
                ),
            ),
        )

    def test_unknown_endpoint_raises(self):
        """Test that a typo'd endpoint name fails validation."""
        with self.assertRaisesRegex(AdminRegistryError, "unknown endpoint"):
            validate_sections(self.app, _section(AdminAction("list", "List", "d", "things.list_thing")))

    def test_disallowed_method_raises(self):
        """Test that a method the route doesn't allow fails validation."""
        with self.assertRaisesRegex(AdminRegistryError, "does not allow DELETE"):
            validate_sections(
                self.app, _section(AdminAction("list", "List", "d", "things.list_things", method="DELETE"))
            )

    def test_missing_path_field_raises(self):
        """Test that omitting a path field required by the URL rule fails validation."""
        with self.assertRaisesRegex(AdminRegistryError, "path fields"):
            validate_sections(self.app, _section(AdminAction("get", "Get", "d", "things.get_thing")))

    def test_misnamed_path_field_raises(self):
        """Test that a path field not matching the rule's argument name fails validation."""
        wrong = AdminField("id", "ID", type="integer", location="path")

        with self.assertRaisesRegex(AdminRegistryError, "path fields"):
            validate_sections(self.app, _section(AdminAction("get", "Get", "d", "things.get_thing", fields=(wrong,))))

    def test_body_field_on_get_raises(self):
        """Test that body fields on a GET action fail validation."""
        with self.assertRaisesRegex(AdminRegistryError, "cannot have body fields"):
            validate_sections(
                self.app,
                _section(AdminAction("list", "List", "d", "things.list_things", fields=(AdminField("q", "Q"),))),
            )

    def test_body_field_on_delete_raises(self):
        """Test that body fields on a DELETE action fail validation."""
        action = AdminAction(
            "delete",
            "Delete",
            "d",
            "things.delete_thing",
            method="DELETE",
            fields=(_THING_ID, AdminField("reason", "Reason")),
        )

        with self.assertRaisesRegex(AdminRegistryError, "cannot have body fields"):
            validate_sections(self.app, _section(action))

    def test_duplicate_action_ids_raise(self):
        """Test that two actions sharing an id within a section fail validation."""
        action = AdminAction("list", "List", "d", "things.list_things")

        with self.assertRaisesRegex(AdminRegistryError, "duplicate action ids"):
            validate_sections(self.app, _section(action, action))

    def test_duplicate_section_ids_raise(self):
        """Test that two sections sharing an id fail validation."""
        section = _section(AdminAction("list", "List", "d", "things.list_things"))[0]

        with self.assertRaisesRegex(AdminRegistryError, "section ids must be unique"):
            validate_sections(self.app, (section, section))

    def test_duplicate_field_names_raise(self):
        """Test that two fields sharing a name within an action fail validation."""
        action = AdminAction("get", "Get", "d", "things.get_thing", fields=(_THING_ID, _THING_ID))

        with self.assertRaisesRegex(AdminRegistryError, "duplicate field names"):
            validate_sections(self.app, _section(action))

    def test_non_dom_safe_ids_raise(self):
        """Test that ids which aren't lowercase kebab-case fail validation."""
        for bad_id in ["Guests", "guest list", "1guests", "guests_list"]:
            with self.subTest(bad_id=bad_id), self.assertRaisesRegex(AdminRegistryError, "kebab-case"):
                validate_sections(
                    self.app,
                    _section(AdminAction("list", "List", "d", "things.list_things"), section_id=bad_id),
                )

    def test_empty_section_raises(self):
        """Test that a section without actions fails validation."""
        with self.assertRaisesRegex(AdminRegistryError, "has no actions"):
            validate_sections(self.app, (AdminSection("things", "Things", "d", actions=()),))


if __name__ == "__main__":
    unittest.main()
