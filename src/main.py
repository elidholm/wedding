"""Entrypoint for running the wedding app directly."""

from flask import render_template

from core.config import config
from core.logging import setup_logging
from rsvp import bp as rsvp_bp
from web_server import create_app


setup_logging()

app = create_app(config)
app.register_blueprint(rsvp_bp, url_prefix="/rsvp")


@app.route("/home")
@app.route("/")
def home() -> str:
    """Render the application's landing page."""
    return render_template("home.html", app_name=config.app_name)


def main() -> None:
    """Run the Flask application."""
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
