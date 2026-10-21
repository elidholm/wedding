"""
db.session - Request-scoped SQLAlchemy session handling
-------------------------------------------------------

Every request that touches the database shares a single SQLAlchemy session,
stashed on Flask's request-scoped ``g`` object. ``init_app`` registers a
teardown hook that closes it (rolling back first on error) once the
application context ends, so callers never have to close it themselves.
"""

from flask import Flask, g
from sqlalchemy.orm import Session

from db.schemas import SessionLocal

_G_KEY = "db_session"


def get_db_session() -> Session:
    """Get (or lazily open) the current request's SQLAlchemy session.

    Returns:
        Session: The current request's SQLAlchemy session.
    """
    if _G_KEY not in g:
        setattr(g, _G_KEY, SessionLocal())
    return getattr(g, _G_KEY)


def close_db_session(exception: BaseException | None = None) -> None:
    """Close the current request's database session, rolling back first on error.

    Args:
        exception (BaseException | None): The exception that ended the
            application context, if any, as passed by Flask's teardown hook.
    """
    session: Session | None = g.pop(_G_KEY, None)
    if session is not None:
        if exception is not None:
            session.rollback()
        session.close()


def init_app(app: Flask) -> None:
    """Register the teardown hook that closes each request's database session.

    Args:
        app (Flask): The Flask application to register the hook on.
    """
    app.teardown_appcontext(close_db_session)
