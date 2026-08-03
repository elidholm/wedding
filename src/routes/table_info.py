from datetime import datetime

from flask import Blueprint, current_app, render_template

bp = Blueprint("table_info", __name__)


@bp.route("/<string:table_name>")
def table_info(table_name: str) -> str:
    """Render the information page for the given table.

    Returns:
        str: The rendered HTML for the page containing information about
        why this table was named the way it was.
    """
    reasons = [
        "reason1",
        "reason2",
        "reason3",
        "reason4",
        "reason5",
    ]
    return render_template(
        "table_info.html",
        app_name=current_app.config["APP_NAME"],
        current_year=datetime.now().year,
        table_name=table_name,
        reasons=reasons,
    )
