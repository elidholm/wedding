"""Unit tests for the core.logging module."""

import logging
import unittest
from unittest.mock import patch

from core.logging import setup_logging


class TestSetupLogging(unittest.TestCase):
    """Test cases for the setup_logging function."""

    @patch("core.logging.RichHandler")
    @patch("core.logging.Console")
    @patch("core.logging.logging.basicConfig")
    def test_configures_root_logger_with_rich_handler(
        self, mock_basic_config, mock_console, mock_rich_handler
    ):
        """Test that setup_logging calls basicConfig with a RichHandler and expected settings."""
        mock_console_instance = mock_console.return_value
        mock_handler_instance = mock_rich_handler.return_value

        setup_logging()

        mock_console.assert_called_once_with()
        mock_rich_handler.assert_called_once_with(console=mock_console_instance)
        mock_basic_config.assert_called_once_with(
            format="%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.INFO,
            handlers=[mock_handler_instance],
        )


if __name__ == "__main__":
    unittest.main()
