"""Entrypoint for running the wedding app directly."""

from flask import Flask

from api.routes import register as register_api
from core.config import get_config
from core.logging import setup_logging
from pages.routes import register as register_pages

config = get_config()

setup_logging(config.log_level)

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)
app.config["APP_NAME"] = config.app_name
app.config["FLASK_ENV"] = config.flask_env
app.config["HOST"] = config.host
app.config["PORT"] = config.port
app.config["DEBUG"] = config.debug
app.config["SECRET_KEY"] = config.secret_key
app.config["CONFIG"] = config

register_pages(app)
register_api(app)


def main() -> None:
    """Run the Flask application."""
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
