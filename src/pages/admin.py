"""
pages.admin - Admin area blueprint (auth scaffold only)
-------------------------------------------------------

This module wires up a password-protected `/admin` area for the wedding
couple.

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


@bp.route("/login", methods=["GET", "POST"])
def login() -> str | Response:
    """Render the admin login form, or handle its password submission.

    On a `POST` with the correct password (as configured via the
    `ADMIN_PASSWORD` environment variable), marks the session as an
    authenticated admin session and redirects to the admin home page.

    On an incorrect password, re-renders the form with an error message.

    Returns:
        str | Response: The rendered HTML for the login page, or a
        redirect response to the admin area.
    """
    config = current_app.config["CONFIG"]
    error = None

    if request.method == "POST":
        submitted_password = request.form.get("password", "")

        if config.admin_password and submitted_password == config.admin_password:
            session["is_admin"] = True
            return redirect(url_for("admin.admin_home"))

        error = "Incorrect password."

    return render_template(
        "admin_login.html",
        config=config,
        current_year=datetime.now(tz=UTC).year,
        error=error,
    )


@bp.route("/logout")
def logout() -> Response:
    """Log the current admin out by clearing their session, then redirect to login.

    Returns:
        Response: A redirect response to the admin login page.
    """
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


@bp.route("/")
@bp.route("")
@login_required
def admin_home() -> str:
    """Render the admin area's dummy landing page.

    Returns:
        str: The rendered HTML for the admin landing page.
    """
    return render_template(
        "admin.html",
        config=current_app.config["CONFIG"],
        current_year=datetime.now(tz=UTC).year,
    )
