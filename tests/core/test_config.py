"""Unit tests for the core.config module."""

import os
import unittest
from unittest.mock import patch

from core.config import Config, config


class TestConfigClass(unittest.TestCase):
    """Test cases for the Config class."""

    def setUp(self):
        self.config = Config()

    def test_field_types(self):
        """Test that every field has the expected type."""
        self.assertIsInstance(self.config.app_name, str)
        self.assertIsInstance(self.config.flask_env, str)
        self.assertIsInstance(self.config.host, str)
        self.assertIsInstance(self.config.port, int)
        self.assertIsInstance(self.config.debug, bool)

    def test_debug_matches_flask_env(self):
        """Test that debug is True only when flask_env is 'development'."""
        self.assertEqual(self.config.debug, self.config.flask_env == "development")

    def test_secret_key_defaults_to_none_when_unset(self):
        """Test that secret_key is None when SECRET_KEY isn't set in the environment."""
        with patch.dict(os.environ, {}, clear=True):
            self.assertIsNone(Config().secret_key)


class TestConfigEnvOverrides(unittest.TestCase):
    """Test cases for Config picking up values from environment variables.

    `pydantic_settings.BaseSettings` reads matching environment variables at
    instantiation time (not just via the `os.getenv(...)` class-level
    defaults), so a fresh `Config()` picks up whatever is in `os.environ`
    when it's constructed -- these tests use `patch.dict` to set that
    without needing to reload the module.
    """

    def test_app_name_env_override(self):
        """Test that APP_NAME in the environment overrides the default app_name."""
        with patch.dict(os.environ, {"APP_NAME": "Overridden App"}):
            self.assertEqual(Config().app_name, "Overridden App")

    def test_host_env_override(self):
        """Test that HOST in the environment overrides the default host."""
        with patch.dict(os.environ, {"HOST": "127.0.0.1"}):
            self.assertEqual(Config().host, "127.0.0.1")

    def test_port_env_override_is_cast_to_int(self):
        """Test that PORT in the environment overrides the default port and is an int."""
        with patch.dict(os.environ, {"PORT": "8080"}):
            new_config = Config()

            self.assertEqual(new_config.port, 8080)
            self.assertIsInstance(new_config.port, int)

    def test_secret_key_env_override(self):
        """Test that SECRET_KEY in the environment overrides the default secret_key."""
        with patch.dict(os.environ, {"SECRET_KEY": "super-secret"}):
            self.assertEqual(Config().secret_key, "super-secret")

    def test_flask_env_override_does_not_retroactively_change_debug(self):
        """Test that overriding FLASK_ENV per-instance does not change `debug`.

        `debug` is computed once, at class-definition time, from the
        `flask_env` value seen at import time -- it is not recomputed from
        each instance's own (possibly overridden) `flask_env`. This test
        documents that existing behavior rather than a desired one.
        """
        with patch.dict(os.environ, {"FLASK_ENV": "development"}):
            new_config = Config()

            self.assertEqual(new_config.flask_env, "development")
            self.assertEqual(new_config.debug, Config.model_fields["debug"].default)


class TestConfigSingleton(unittest.TestCase):
    """Test cases for the singleton config instance."""

    def test_singleton_instance(self):
        """Test that the config instance is of type Config."""
        self.assertIsInstance(config, Config)


if __name__ == "__main__":
    unittest.main()
