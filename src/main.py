"""Entrypoint for running the wedding app directly."""

from pathlib import Path

from flask import Flask

from api.v1.health import bp as health_bp
from core.config import Config
from core.logging import setup_logging
from pages.contact import bp as contact_bp
from pages.home import bp as home_bp
from pages.itinerary import bp as itinerary_bp
from pages.rsvp import bp as rsvp_bp
from pages.seating import bp as seating_bp
from pages.table_info import bp as table_info_bp

CONFIG_FILE = Path(__file__).parent / "config.yml"
config = Config.load(CONFIG_FILE)

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

app.register_blueprint(home_bp, url_prefix="")
app.register_blueprint(rsvp_bp, url_prefix="/rsvp")
app.register_blueprint(contact_bp, url_prefix="/contact")
app.register_blueprint(itinerary_bp, url_prefix="/itinerary")
app.register_blueprint(seating_bp, url_prefix="/seating")
app.register_blueprint(table_info_bp, url_prefix="/tables")

app.register_blueprint(health_bp, url_prefix="/api/v1/health")


def main() -> None:
    """Run the Flask application."""
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
