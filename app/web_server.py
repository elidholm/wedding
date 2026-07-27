"""Application factory for the wedding app."""

from flask import Flask, render_template

from config import AppConfig
from rsvp import bp as rsvp_bp


def create_app(config: AppConfig) -> Flask:
    """Create and configure the Flask application instance.

    Args:
        config (AppConfig): The application configuration object.

    Returns:
        Flask: The configured Flask application instance.
    """
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

    app.register_blueprint(rsvp_bp, url_prefix="/rsvp")

    @app.route("/home")
    @app.route("/")
    def home() -> str:
        """Render the application's landing page."""
        return render_template("index.html", app_name=config.app_name)

    return app
