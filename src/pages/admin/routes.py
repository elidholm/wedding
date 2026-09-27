"""
pages.admin.routes - Admin area blueprint
-----------------------------------------

This module wires up a password-protected `/admin` area for the wedding
couple. The landing page is rendered from the declarative registry in
``pages.admin.sections``; see that module for how to add a new section or
action.

The area is intentionally not linked from the site's navigation; it is
only reachable by visiting `/admin` directly.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.wrappers import Response

from pages.admin.sections import SECTIONS, resolve_url_template

bp = Blueprint("admin", __name__)


def login_required(view: Callable[..., str | Response]) -> Callable[..., str | Response]:
    """Redirect to the admin login page unless the current session is authenticated.

    Args:
        view (Callable[..., str | Response]): The view function to guard.

    Returns:
        Callable[..., str | Response]: The wrapped view function.
    """

    @wraps(view)
    def wrapped_view(*args: object, **kwargs: object) -> str | Response:
        if not session.get("is_admin"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


@bp.get("/login")
def login() -> str:
    """Render the admin login form.

    Authentication is handled by the JSON API in ``api.v1.auth``.
    """
    return render_template(
        "admin_login.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
    )


@bp.route("/")
@bp.route("")
@login_required
def admin_home() -> str:
    """Render the admin landing page from the section registry.

    Returns:
        str: The rendered HTML for the admin landing page.
    """
    url_templates = {
        (section.id, action.id): resolve_url_template(current_app, action)
        for section in SECTIONS
        for action in section.actions
    }
    return render_template(
        "admin.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
        sections=SECTIONS,
        url_templates=url_templates,
    )
