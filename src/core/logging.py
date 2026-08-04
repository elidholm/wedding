"""Logging configuration for the application."""

import logging

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(log_level: str | int = logging.INFO) -> None:
    """Set up logging configuration for the application.

    Args:
        log_level (str | int): The logging level to use. Defaults to logging.INFO.
    """
    console = Console()
    logging.basicConfig(
        format="%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=log_level,
        handlers=[RichHandler(console=console)],
    )
