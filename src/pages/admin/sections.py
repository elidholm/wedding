"""
pages.admin.sections - Declarative registry of admin sections and actions
-------------------------------------------------------------------------

The admin page is rendered entirely from ``SECTIONS``. Each ``AdminSection``
(e.g. "Gästlista") holds one or more ``AdminAction`` sub-sections, one per
API endpoint. The template and ``static/js/admin.js`` are fully generic, so
adding a new admin tool is a single registry edit here - no template or
JavaScript changes required.

Adding an action:
    Append an ``AdminAction`` to a section's ``actions`` tuple. Path
    parameters in the endpoint's URL rule must be declared as
    ``location="path"`` fields with matching names; everything else is sent
    as a JSON body (``POST``/``PUT`` only). Blank body fields are omitted
    from the request, so update actions only change what was filled in::

        AdminAction(
            id="get",
            title="Hämta en gäst",
            description="Visa all information om en enskild gäst.",
            endpoint="guests.get_guest",
            submit_label="Hämta gäst",
            fields=(AdminField("guest_id", "Gäst-ID", type="integer", location="path", required=True),),
        ),
        AdminAction(
            id="update",
            title="Uppdatera en gäst",
            description="Ändra de fält du fyller i; tomma fält lämnas orörda.",
            endpoint="guests.update_guest",
            method="PUT",
            submit_label="Spara ändringar",
            fields=(
                AdminField("guest_id", "Gäst-ID", type="integer", location="path", required=True),
                AdminField("name", "Namn"),
                AdminField("attending", "Kommer", type="tri_bool"),
                AdminField("allergies", "Allergier", type="textarea"),
            ),
        ),
        AdminAction(
            id="delete",
            title="Ta bort en gäst",
            description="Raderar gästen permanent.",
            endpoint="guests.delete_guest",
            method="DELETE",
            submit_label="Ta bort gäst",
            destructive=True,
            fields=(AdminField("guest_id", "Gäst-ID", type="integer", location="path", required=True),),
        ),

    Use ``tri_bool`` (yes/no/unset) rather than ``bool`` in update actions:
    a checkbox has no "unset" state, so a ``bool`` field is always sent.

    ``validate_sections`` runs at app startup (see ``main.py``) and fails
    fast on typos such as an unknown endpoint, a method the route doesn't
    allow, or path fields that don't match the URL rule.
"""

import re
from dataclasses import dataclass
from typing import Literal

from flask import Flask
from werkzeug.routing import Rule

FieldType = Literal["text", "email", "integer", "tri_bool", "bool", "textarea"]
FieldLocation = Literal["path", "body"]
HttpMethod = Literal["GET", "POST", "PUT", "DELETE"]

_DOM_ID_RE = re.compile(r"^[a-z][a-z0-9-]*$")
_RULE_ARG_RE = re.compile(r"<(?:[^:<>]+:)?([^<>]+)>")
_BODYLESS_METHODS = frozenset({"GET", "DELETE"})


class AdminRegistryError(ValueError):
    """Raised when the admin section registry is misconfigured."""


@dataclass(frozen=True)
class AdminField:
    """A single input rendered for an admin action.

    Attributes:
        name (str): The URL rule argument name (``location="path"``) or JSON
            body key (``location="body"``).
        label (str): The human-readable field label.
        type (FieldType): The input type, which controls both rendering and
            how the value is serialized. Defaults to ``"text"``.
        location (FieldLocation): Whether the value fills a URL path
            parameter or goes into the JSON body. Defaults to ``"body"``.
        required (bool): Whether the field must be filled in before the
            action can be submitted. Defaults to False.
        help (str | None): Optional helper text shown under the field.
    """

    name: str
    label: str
    type: FieldType = "text"
    location: FieldLocation = "body"
    required: bool = False
    help: str | None = None


@dataclass(frozen=True)
class AdminAction:
    """A sub-section of an admin section that calls exactly one API endpoint.

    Attributes:
        id (str): DOM-safe identifier, unique within its section.
        title (str): The sub-section heading.
        description (str): A short explanation of what the action does.
        endpoint (str): The Flask endpoint name, e.g. ``"guests.list_guests"``.
        method (HttpMethod): The HTTP method to call the endpoint with.
            Defaults to ``"GET"``.
        submit_label (str): The label of the action's button. Defaults to
            ``"Kör"``.
        fields (tuple[AdminField, ...]): Inputs for path parameters and JSON
            body values. Defaults to no inputs.
        destructive (bool): Whether the action requires a second, confirming
            press before it runs. Defaults to False.
    """

    id: str
    title: str
    description: str
    endpoint: str
    method: HttpMethod = "GET"
    submit_label: str = "Kör"
    fields: tuple[AdminField, ...] = ()
    destructive: bool = False


@dataclass(frozen=True)
class AdminSection:
    """A top-level group of related admin actions, e.g. guest management.

    Attributes:
        id (str): DOM-safe identifier, unique across all sections.
        title (str): The section heading.
        description (str): A short explanation of the section's purpose.
        actions (tuple[AdminAction, ...]): The section's sub-sections, one per
            API endpoint, rendered in order.
    """

    id: str
    title: str
    description: str
    actions: tuple[AdminAction, ...]


SECTIONS: tuple[AdminSection, ...] = (
    AdminSection(
        id="guests",
        title="Gästlista",
        description="Hantera gästerna som finns i databasen.",
        actions=(
            AdminAction(
                id="list",
                title="Lista alla gäster",
                description="Hämta samtliga gäster som just nu finns i databasen.",
                endpoint="guests.list_guests",
                submit_label="Generera gästlista",
            ),
            AdminAction(
                id="user",
                title="Hämta en gäst",
                description="Visa all information om en enskild gäst.",
                endpoint="guests.get_guest",
                submit_label="Hämta gäst",
                fields=(AdminField("guest_id", "Gäst-ID", type="integer", location="path", required=True),),
            ),
            AdminAction(
                id="create",
                title="Lägg till en gäst",
                description="Skapa en ny gäst med de fält du fyller i.",
                endpoint="guests.create_guest",
                method="POST",
                submit_label="Lägg till gäst",
                fields=(
                    AdminField("name", "Namn", required=True),
                    AdminField("email", "E-postadress", type="email"),
                    AdminField("attending", "Kommer", type="tri_bool"),
                    AdminField("plus_one_allowed", "Plus one tillåten", type="bool"),
                    AdminField("plus_one_name", "Namn på plus one"),
                    AdminField("food_preferences", "Matpreferenser", type="textarea"),
                ),
            ),
            AdminAction(
                id="update",
                title="Uppdatera en gäst",
                description="Ändra de fält du fyller i; tomma fält lämnas orörda.",
                endpoint="guests.update_guest",
                method="PUT",
                submit_label="Spara ändringar",
                fields=(
                    AdminField("guest_id", "Gäst-ID", type="integer", location="path", required=True),
                    AdminField("name", "Namn"),
                    AdminField("email", "E-postadress", type="email"),
                    AdminField("attending", "Kommer", type="tri_bool"),
                    AdminField("plus_one_allowed", "Plus one tillåten", type="tri_bool"),
                    AdminField("plus_one_name", "Namn på plus one"),
                    AdminField("food_preferences", "Matpreferenser", type="textarea"),
                ),
            ),
            AdminAction(
                id="delete",
                title="Ta bort en gäst",
                description="Raderar gästen permanent.",
                endpoint="guests.delete_guest",
                method="DELETE",
                submit_label="Ta bort gäst",
                destructive=True,
                fields=(AdminField("guest_id", "Gäst-ID", type="integer", location="path", required=True),),
            ),
        ),
    ),
)


def _rule_for(app: Flask, action: AdminAction) -> Rule:
    """Find the URL rule an action's endpoint is registered under.

    Args:
        app (Flask): The application whose URL map to search.
        action (AdminAction): The action whose endpoint to look up.

    Returns:
        Rule: The first URL rule registered for the action's endpoint.

    Raises:
        AdminRegistryError: If no rule is registered for the endpoint.
    """
    rules = app.url_map.iter_rules(action.endpoint) if action.endpoint in app.view_functions else iter(())
    rule = next(rules, None)
    if rule is None:
        raise AdminRegistryError(f"Admin action {action.id!r} names unknown endpoint {action.endpoint!r}.")
    return rule


def resolve_url_template(app: Flask, action: AdminAction) -> str:
    """Build the client-side URL template for an action.

    Converter-typed rule arguments become ``{name}`` placeholders, e.g.
    ``/api/v1/guests/<int:guest_id>`` becomes ``/api/v1/guests/{guest_id}``.
    ``url_for`` can't be used here, since typed converters reject
    placeholder values.

    Args:
        app (Flask): The application whose URL map to resolve against.
        action (AdminAction): The action to resolve.

    Returns:
        str: The URL template, which the browser fills in from path fields.
    """
    return _RULE_ARG_RE.sub(r"{\1}", _rule_for(app, action).rule)


def _validate_id(kind: str, value: str) -> None:
    """Ensure an identifier is safe to embed in DOM ids.

    Args:
        kind (str): What the id identifies, used in the error message.
        value (str): The identifier to check.

    Raises:
        AdminRegistryError: If the identifier is not lowercase kebab-case.
    """
    if not _DOM_ID_RE.match(value):
        raise AdminRegistryError(f"{kind} id {value!r} must be lowercase kebab-case (e.g. 'guest-list').")


def _validate_action(app: Flask, section: AdminSection, action: AdminAction) -> None:
    """Validate a single action against the app's URL map.

    Args:
        app (Flask): The application to validate against.
        section (AdminSection): The section the action belongs to.
        action (AdminAction): The action to validate.

    Raises:
        AdminRegistryError: If the action is misconfigured.
    """
    _validate_id("Action", action.id)
    where = f"{section.id}/{action.id}"
    rule = _rule_for(app, action)

    if action.method not in (rule.methods or set()):
        raise AdminRegistryError(f"Admin action {where!r}: {action.endpoint!r} does not allow {action.method}.")

    field_names = [field.name for field in action.fields]
    if len(field_names) != len(set(field_names)):
        raise AdminRegistryError(f"Admin action {where!r} has duplicate field names.")

    path_fields = {field.name for field in action.fields if field.location == "path"}
    if path_fields != set(rule.arguments):
        raise AdminRegistryError(
            f"Admin action {where!r}: path fields {sorted(path_fields)} must match "
            f"the URL rule arguments {sorted(rule.arguments)} of {rule.rule!r}."
        )

    has_body = any(field.location == "body" for field in action.fields)
    if has_body and action.method in _BODYLESS_METHODS:
        raise AdminRegistryError(f"Admin action {where!r}: {action.method} actions cannot have body fields.")


def validate_sections(app: Flask, sections: tuple[AdminSection, ...] = SECTIONS) -> None:
    """Fail fast if any admin section or action is misconfigured.

    Must run after every page and API blueprint has been registered, since
    it resolves each action's endpoint against ``app.url_map``.

    Args:
        app (Flask): The fully wired application to validate against.
        sections (tuple[AdminSection, ...]): The registry to validate.
            Defaults to ``SECTIONS``.

    Raises:
        AdminRegistryError: On an unknown endpoint, a disallowed method, path
            fields that don't match the URL rule, body fields on a GET or
            DELETE action, or duplicate/non-DOM-safe ids.
    """
    section_ids = [section.id for section in sections]
    if len(section_ids) != len(set(section_ids)):
        raise AdminRegistryError("Admin section ids must be unique.")

    for section in sections:
        _validate_id("Section", section.id)
        if not section.actions:
            raise AdminRegistryError(f"Admin section {section.id!r} has no actions.")

        action_ids = [action.id for action in section.actions]
        if len(action_ids) != len(set(action_ids)):
            raise AdminRegistryError(f"Admin section {section.id!r} has duplicate action ids.")

        for action in section.actions:
            _validate_action(app, section, action)
