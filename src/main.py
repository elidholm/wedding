"""Entrypoint for running the wedding app directly."""

from core.config import config
from core.logging import setup_logging
from routes.home import bp as home_bp
from routes.rsvp import bp as rsvp_bp
from web_server import create_app


setup_logging()

app = create_app(config)
app.register_blueprint(home_bp, url_prefix="")
app.register_blueprint(rsvp_bp, url_prefix="/rsvp")


def main() -> None:
    """Run the Flask application."""
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
