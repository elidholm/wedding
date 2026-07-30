"""Application configuration, sourced from environment variables (.env)."""

import os

from pydantic import BaseModel


class AppConfig(BaseModel):
    """Runtime configuration read from the environment.

    Attributes:
        app_name (str): The name of the application.
        flask_env (str): The Flask environment (e.g., "development", "production").
        host (str): The host address to bind the Flask app to.
        port (int): The port number to bind the Flask app to.
        debug (bool): Whether to run the Flask app in debug mode.
    """

    app_name: str = os.getenv("APP_NAME", "Flask App")
    flask_env: str = os.getenv("FLASK_ENV", "production")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "5000"))

    debug: bool = flask_env == "development"
