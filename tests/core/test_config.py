"""Unit tests for the core.config module."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import Config, ContactInfo


class TestConfigClassLoad(unittest.TestCase):
    """Test cases for the Config class .load() static method."""

    def test_load_from_yaml_file(self):
        """Test that the Config.load() correctly loads from a YAML file."""
        config_file_path = Path(__file__).parent.parent / "data" / "full_config.yml"
        loaded_config = Config.load(config_file_path)

        self.assertIsInstance(loaded_config, Config)

        test_fields = [
            ("app_name", "Test App"),
            ("flask_env", "staging"),
            ("host", "1.2.3.4"),
            ("port", 1234),
            ("secret_key", "test_secret"),
            ("log_level", "WARNING"),
            ("debug", False),
            ("wedding_couple_contact", ContactInfo(email="test@email.com", phone="(+46)70-123 45 67")),
        ]
        for field_name, expected_value in test_fields:
            with self.subTest(field=field_name):
                actual_value = getattr(loaded_config, field_name)
                self.assertEqual(actual_value, expected_value)

    def test_load_with_string_file_path(self):
        """Test that Config.load() works with a string file path."""
        config_file_path = str(Path(__file__).parent.parent / "data" / "full_config.yml")
        loaded_config = Config.load(config_file_path)

        self.assertIsInstance(loaded_config, Config)

        test_fields = [
            ("app_name", "Test App"),
            ("flask_env", "staging"),
            ("host", "1.2.3.4"),
            ("port", 1234),
            ("secret_key", "test_secret"),
            ("log_level", "WARNING"),
            ("debug", False),
        ]
        for field_name, expected_value in test_fields:
            with self.subTest(field=field_name):
                actual_value = getattr(loaded_config, field_name)
                self.assertEqual(actual_value, expected_value)

    def test_load_raises_runtime_error_for_missing_file(self):
        """Test that Config.load() raises RuntimeError for a missing config file."""
        missing_file_path = Path(__file__).parent.parent / "data" / "non_existent_config.yml"
        with self.assertRaises(RuntimeError) as context:
            Config.load(missing_file_path)

        self.assertIn("No configuration file provided", str(context.exception))

    def test_load_raises_runtime_error_for_invalid_yaml(self):
        """Test that Config.load() raises RuntimeError for an invalid YAML file."""
        invalid_yaml_path = Path(__file__).parent.parent / "data" / "invalid_config.yml"
        with self.assertRaises(RuntimeError) as context:
            Config.load(invalid_yaml_path)

        self.assertIn("Failed to load configuration", str(context.exception))

    def test_load_with_partial_config(self):
        """Test that Config.load() correctly loads from a partial YAML file."""
        partial_config_path = Path(__file__).parent.parent / "data" / "partial_config.yml"
        loaded_config = Config.load(partial_config_path)

        self.assertIsInstance(loaded_config, Config)

        test_fields = [
            ("app_name", "Test App With Partial Config"),
            ("flask_env", "development"),  # Default value
            ("host", "0.0.0.0"),  # Default value
            ("port", 5000),  # Default value
            ("secret_key", None),  # Default value
            ("log_level", "INFO"),  # Default value
            ("debug", True),  # Default value
            ("wedding_couple_contact", None),  # Default value
        ]
        for field_name, expected_value in test_fields:
            with self.subTest(field=field_name):
                actual_value = getattr(loaded_config, field_name)
                self.assertEqual(actual_value, expected_value)


class TestConfigLoadEnvOverrides(unittest.TestCase):
    """Test cases for Config.load() picking up values from environment variables.

    `pydantic_settings.BaseSettings` reads matching environment variables at
    instantiation time (not just via the `os.getenv(...)` class-level
    defaults), so a fresh `Config()` picks up whatever is in `os.environ`
    when it's constructed -- these tests use `patch.dict` to set that
    without needing to reload the module.
    """

    def setUp(self):
        self.config_file = Path(__file__).parent.parent / "data" / "full_config.yml"

    def test_app_name_env_override(self):
        """Test that APP_NAME in the environment overrides the default app_name."""
        with patch.dict(os.environ, {"APP_NAME": "Overridden App"}):
            self.assertEqual(Config.load(self.config_file).app_name, "Overridden App")

    def test_host_env_override(self):
        """Test that HOST in the environment overrides the default host."""
        with patch.dict(os.environ, {"HOST": "127.0.0.1"}):
            self.assertEqual(Config.load(self.config_file).host, "127.0.0.1")

    def test_port_env_override_is_cast_to_int(self):
        """Test that PORT in the environment overrides the default port and is an int."""
        with patch.dict(os.environ, {"PORT": "8080"}):
            new_config = Config.load(self.config_file)

            self.assertEqual(new_config.port, 8080)
            self.assertIsInstance(new_config.port, int)

    def test_secret_key_env_override(self):
        """Test that SECRET_KEY in the environment overrides the default secret_key."""
        with patch.dict(os.environ, {"SECRET_KEY": "super-secret"}):
            self.assertEqual(Config.load(self.config_file).secret_key, "super-secret")


class TestContactInfo(unittest.TestCase):
    """Test cases for the ContactInfo class."""

    def setUp(self):
        """Set up a valid ContactInfo instance for testing."""
        self.valid_email = "test_address@email.com"
        self.valid_phone = "(+46)70-123 45 67"

    def test_valid_email_and_phone(self):
        """Test that a valid email and phone number are accepted."""
        contact_info = ContactInfo(email=self.valid_email, phone=self.valid_phone)

        self.assertEqual(contact_info.email, self.valid_email)
        self.assertEqual(contact_info.phone, self.valid_phone)

    def test_invalid_email_raises_value_error(self):
        """Test that an invalid email raises a ValueError."""
        with self.assertRaises(ValueError):
            ContactInfo(email="invalid-email", phone=self.valid_phone)

    def test_invalid_phone_raises_value_error(self):
        """Test that an invalid phone number raises a ValueError."""
        with self.assertRaises(ValueError):
            ContactInfo(email=self.valid_email, phone="invalid-phone")


if __name__ == "__main__":
    unittest.main()
