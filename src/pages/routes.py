"""
pages.routes - Aggregates and registers all page blueprints on the Flask app
----------------------------------------------------------------------------

This module is the single place where the individual page blueprints are wired
up to a Flask application, each under its own URL prefix.
"""

from flask import Flask

from pages.contact import bp as contact_bp
from pages.home import bp as home_bp
from pages.itinerary import bp as itinerary_bp
from pages.rsvp import bp as rsvp_bp
from pages.seating import bp as seating_bp
from pages.table_info import bp as table_info_bp


def register(app: Flask) -> None:
    """Register all page blueprints on the given Flask app.

    Args:
        app (Flask): The Flask application to register the page blueprints on.
    """
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(rsvp_bp, url_prefix="/rsvp")
    app.register_blueprint(contact_bp, url_prefix="/contact")
    app.register_blueprint(itinerary_bp, url_prefix="/itinerary")
    app.register_blueprint(seating_bp, url_prefix="/seating")
    app.register_blueprint(table_info_bp, url_prefix="/tables")
