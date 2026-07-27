"""Entrypoint for running the wedding app directly."""

from config import AppConfig
from web_server import create_app


def main() -> None:
    """Create the app and run Flask's dev server."""
    config = AppConfig()

    app = create_app(config)
    app.run(host=config.host, port=config.port, debug=config.debug)


if __name__ == "__main__":
    main()
