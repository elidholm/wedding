"""Logging configuration for the application."""

import logging

from rich.console import Console
from rich.logging import RichHandler


def setup_logging() -> None:
    """Set up logging configuration for the application."""
    console = Console()
    logging.basicConfig(
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO,
        handlers=[RichHandler(console=console)],
    )
