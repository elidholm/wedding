"""Unit tests for the core.config module."""

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from core.config import Config, ContactInfo, FaqEntry, WeddingVenue


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
            (
                "toast_master_contact",
                [
                    ContactInfo(name="Toast Master 1", email="toast_master_1@wedding.com", phone="(+46)71-111 11 11"),
                    ContactInfo(name="Toast Master 2", email="toast_master_2@wedding.com", phone="(+46)72-222 22 22"),
                ],
            ),
            (
                "venue",
                WeddingVenue(
                    name="The Wedding Venue",
                    address="123 Wedding St",
                    city="Wedding City",
                ),
            ),
            (
                "faq",
                [
                    FaqEntry(question="Test question one?", answer="Test answer one."),
                    FaqEntry(question="Test question two?", answer="Test answer two."),
                ],
            ),
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
            ("wedding_couple_contact", ContactInfo(email="test@email.com", phone="(+46)70-123 45 67")),
            (
                "toast_master_contact",
                [
                    ContactInfo(name="Toast Master 1", email="toast_master_1@wedding.com", phone="(+46)71-111 11 11"),
                    ContactInfo(name="Toast Master 2", email="toast_master_2@wedding.com", phone="(+46)72-222 22 22"),
                ],
            ),
            (
                "venue",
                WeddingVenue(
                    name="The Wedding Venue",
                    address="123 Wedding St",
                    city="Wedding City",
                ),
            ),
            (
                "faq",
                [
                    FaqEntry(question="Test question one?", answer="Test answer one."),
                    FaqEntry(question="Test question two?", answer="Test answer two."),
                ],
            ),
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
            ("wedding_couple_contact", ContactInfo(email="test@email.com", phone="(+46)70-123 45 67")),
            ("toast_master_contact", []),  # Default value
            ("venue", None),  # Default value
            ("faq", []),  # Default value
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

    def test_wrong_type_env_override_logs_error(self):
        """Test that an environment variable with the wrong type logs an error and does not override."""
        with patch.dict(os.environ, {"PORT": "not-an-int"}), self.assertLogs("core.config", level="ERROR") as log:
            new_config = Config.load(self.config_file)

            self.assertIn("Invalid value for PORT", log.output[0])
            self.assertEqual(new_config.port, 1234)


class TestContactInfo(unittest.TestCase):
    """Test cases for the ContactInfo class."""

    def setUp(self):
        """Set up a valid ContactInfo instance for testing."""
        self.name = "Test User"
        self.valid_email = "test_address@email.com"
        self.valid_phone = "(+46)70-123 45 67"

    def test_valid_email_and_phone(self):
        """Test that a valid email and phone number are accepted."""
        contact_info = ContactInfo(name=self.name, email=self.valid_email, phone=self.valid_phone)

        self.assertEqual(contact_info.name, self.name)
        self.assertEqual(contact_info.email, self.valid_email)
        self.assertEqual(contact_info.phone, self.valid_phone)

    def test_missing_name_is_allowed(self):
        """Test that a missing name is allowed and defaults to None."""
        contact_info = ContactInfo(email=self.valid_email, phone=self.valid_phone)

        self.assertIsNone(contact_info.name)
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

    def test_missing_email_raises_value_error(self):
        """Test that a missing email raises a ValueError."""
        with self.assertRaises(ValueError):
            ContactInfo(email=None, phone=self.valid_phone)

    def test_missing_phone_raises_value_error(self):
        """Test that a missing phone number raises a ValueError."""
        with self.assertRaises(ValueError):
            ContactInfo(email=self.valid_email, phone=None)


class TestWeddingVenue(unittest.TestCase):
    """Test cases for the WeddingVenue class."""

    def setUp(self):
        self.name = "The Wedding Venue"
        self.address = "123 Wedding St"
        self.city = "Wedding City"

    def test_valid_venue(self):
        """Test that a valid WeddingVenue instance is created correctly."""
        venue = WeddingVenue(name=self.name, address=self.address, city=self.city)

        self.assertEqual(venue.name, self.name)
        self.assertEqual(venue.address, self.address)
        self.assertEqual(venue.city, self.city)

    def test_missing_city_is_allowed(self):
        """Test that a missing city is allowed and defaults to None."""
        venue = WeddingVenue(name=self.name, address=self.address)

        self.assertEqual(venue.name, self.name)
        self.assertEqual(venue.address, self.address)
        self.assertIsNone(venue.city)


class TestFaqEntry(unittest.TestCase):
    """Test cases for the FaqEntry class."""

    def setUp(self):
        self.question = "What is the dress code?"
        self.answer = "Formal attire is preferred."

    def test_valid_faq_entry(self):
        """Test that a valid FaqEntry instance is created correctly."""
        faq_entry = FaqEntry(question=self.question, answer=self.answer)

        self.assertEqual(faq_entry.question, self.question)
        self.assertEqual(faq_entry.answer, self.answer)


if __name__ == "__main__":
    unittest.main()
