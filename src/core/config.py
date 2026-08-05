"""Application configuration.

Configuration is read from environment variables and a YAML file.
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from pydantic import BaseModel, ValidationError, field_validator
from pydantic_yaml import parse_yaml_file_as

_log = logging.getLogger(__name__)


EMAIL_RE: re.Pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE: re.Pattern = re.compile(r"^\(\+[0-9]+\)7[0-9]-[0-9]{3} [0-9]{2} [0-9]{2}$")
ENV_VAR_OVERRIDES = {
    ("app_name", str),
    ("flask_env", str),
    ("host", str),
    ("port", int),
    ("secret_key", str),
    ("log_level", str),
}


class ContactInfo(BaseModel):
    """Contact information for a person.

    Attributes:
        name (str | None): The name of the contact person. Defaults
            to None if not provided.
        email (str): The email address of the contact person. Must
            be a valid email format.
        phone (str): The phone number of the contact person. Must
            match the format "(+<country_code>)7X-XXX XX XX".
    """

    name: str | None = None
    email: str
    phone: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Validate that the email address is in a valid format."""
        if not EMAIL_RE.match(value):
            raise ValueError(f"Invalid email address: {value}")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """Validate that the phone number matches the expected format."""
        if not PHONE_RE.match(value):
            raise ValueError(f"Invalid phone number: {value}")
        return value


class WeddingVenue(BaseModel):
    """Information about the wedding venue.

    Attributes:
        name (str): The name of the wedding venue. Defaults to
            "The Wedding Venue".
        address (str): The address of the wedding venue.
        city (str | None): The city where the wedding venue is
            located. Defaults to None if not provided.
    """

    name: str
    address: str
    city: str | None = None


class Config(BaseModel):
    """Runtime configuration read from the environment.

    Attributes:
        app_name (str): The name of the application. Defaults to "Flask App".
        flask_env (str): The Flask environment (e.g., "development", "production").
            Defaults to "development".
        host (str): The host address to bind the Flask app to. Defaults to "0.0.0.0"
        port (int): The port number to bind the Flask app to. Defaults to 5000.
        secret_key (str | None): The secret key for Flask sessions, or None if not set.
            Defaults to None.
        log_level (str): The logging level for the application. Defaults to "INFO".
        debug (bool): Whether to run the Flask app in debug mode. Defaults to True.
        wedding_couple_contact (ContactInfo): Contact information for the wedding couple.
        toast_master_contact (list[ContactInfo]): Contact information for the toast
            master(s). Defaults to an empty list.
        venue (WeddingVenue | None): Information about the wedding venue. Defaults to
            None if not provided.
    """

    app_name: str = "Flask App"
    flask_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 5000
    secret_key: str | None = None
    log_level: str = "INFO"
    debug: bool = True

    wedding_couple_contact: ContactInfo
    toast_master_contact: list[ContactInfo] = []

    venue: WeddingVenue | None = None

    @staticmethod
    def load(config_file: str | Path) -> Config:
        """Load the configuration from environment variables and YAML file.

        Args:
            config_file (str | Path): The path to the YAML configuration file.

        Returns:
            Config: An instance of the Config class with loaded values.

        Raises:
            RuntimeError: If the configuration file does not exist or cannot be loaded.
        """
        if not Path(config_file).exists():
            raise RuntimeError("No configuration file provided.")

        try:
            config = parse_yaml_file_as(Config, config_file)
        except ValidationError as e:
            raise RuntimeError(f"Failed to load configuration from {config_file}: {e}")

        for field, field_type in ENV_VAR_OVERRIDES:
            env_var = field.upper()
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    setattr(config, field, field_type(env_value))
                except ValueError as e:
                    _log.error(f"Invalid value for {env_var}: {e}")

        return config
