"""Entrypoint for running the wedding app directly."""

from flask import Flask

from core.config import config
from core.logging import setup_logging
from routes.contact import bp as contact_bp
from routes.home import bp as home_bp
from routes.rsvp import bp as rsvp_bp


setup_logging()

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

app.register_blueprint(home_bp, url_prefix="")
app.register_blueprint(rsvp_bp, url_prefix="/rsvp")
app.register_blueprint(contact_bp, url_prefix="/contact")


def main() -> None:
    """Run the Flask application."""
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
