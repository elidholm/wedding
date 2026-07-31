"""Application factory for the wedding app."""

from flask import Flask

from core.config import AppConfig


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
    app.config["SECRET_KEY"] = config.secret_key

    return app
