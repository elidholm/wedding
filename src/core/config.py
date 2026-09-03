"""
core.config - Application configuration
---------------------------------------

Configuration is read from environment variables and a YAML file.

Attributes:
    CONFIG_FILE (Path): Path to the YAML configuration file.
    EMAIL_RE (re.Pattern): Regular expression pattern for validating email addresses.
    PHONE_RE (re.Pattern): Regular expression pattern for validating phone numbers.
    ENV_VAR_OVERRIDES (set[tuple[str, type]]): Set of tuples containing environment variable names
        and their corresponding types for overriding configuration values.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, computed_field, field_validator, model_validator
from pydantic_yaml import parse_yaml_file_as

_log = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.yml"
EMAIL_RE: re.Pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE: re.Pattern = re.compile(r"^\(\+[0-9]+\)7[0-9]-[0-9]{3} [0-9]{2} [0-9]{2}$")
ENV_VAR_OVERRIDES: set[tuple[str, type]] = {
    ("app_name", str),
    ("flask_env", str),
    ("host", str),
    ("port", int),
    ("secret_key", str),
    ("log_level", str),
    ("googlemaps_key", str),
    ("db_url", str),
    ("admin_password", str),
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


class FaqEntry(BaseModel):
    """A single question-and-answer pair shown in the FAQ section.

    Attributes:
        question (str): The question as shown on the accordion header.
        answer (str): The answer revealed when the entry is expanded.
    """

    question: str
    answer: str


class WeddingVenue(BaseModel):
    """Information about the wedding venue.

    Attributes:
        name (str): The name of the wedding venue.
        address (str): The address of the wedding venue.
        city (str | None): The city where the wedding venue is located. Defaults to
            None if not provided.
    """

    name: str
    address: str
    city: str | None = None


class WeddingDate(BaseModel):
    """Information about the wedding date and time.

    Attributes:
        day (int): The day of the wedding date.
        month (int): The month of the wedding date.
        year (int): The year of the wedding date.
        time (str): The time of the wedding in HH:MM format.
        weekday (int | None): The weekday of the wedding date, where Monday is 0 and Sunday is 6.
    """

    day: int = Field(..., ge=1, le=31)
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=0)
    time: str

    @field_validator("time")
    @classmethod
    def validate_time(cls, value: str) -> str:
        """Validate that the time is in HH:MM format."""
        if not re.match(r"^\d{2}:\d{2}$", value):
            raise ValueError(f"Invalid time format: {value}. Expected HH:MM.")

        hour, minute = map(int, value.split(":"))
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            raise ValueError(f"Invalid time: {value}. Hour must be 0-23 and minute 0-59.")

        return value

    @model_validator(mode="after")
    def validate_date(self) -> WeddingDate:
        """Validate that the date is a valid calendar date."""
        try:
            datetime(self.year, self.month, self.day, tzinfo=UTC)
        except ValueError as e:
            raise ValueError(f"Invalid wedding date: {e}")

        return self

    @computed_field
    def weekday(self) -> int | None:
        """Return the weekday of the wedding date, or None if the date is invalid."""
        try:
            return datetime(self.year, self.month, self.day, tzinfo=UTC).weekday()
        except ValueError:
            return None


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
        admin_password (str | None): The password required to log in to the admin
            area, or None if not set (in which case admin login is disabled).
            Defaults to None.
        log_level (str): The logging level for the application. Defaults to "INFO".
        debug (bool): Whether to run the Flask app in debug mode. Defaults to True.
        googlemaps_key (str): The Google Maps API key. Defaults to an empty string.
        db_url (str): The SQLAlchemy database URL. Defaults to a local SQLite file under
            ``storage/``.
        wedding_couple_contact (ContactInfo): Contact information for the wedding couple.
        toast_master_contact (list[ContactInfo]): Contact information for the toast
            master(s). Defaults to an empty list.
        date (WeddingDate | None): Information about the wedding date and time. Defaults
            to None if not provided.
        venue (WeddingVenue | None): Information about the wedding venue. Defaults to
            None if not provided.
        faq (list[FaqEntry]): Question-and-answer pairs rendered as the home page's
            FAQ accordion. Defaults to an empty list, in which case the FAQ section
            is omitted entirely.
    """

    app_name: str = "Flask App"
    flask_env: str = "development"
    host: str = "0.0.0.0"
    port: int = 5000
    secret_key: str | None = None
    admin_password: str | None = None
    log_level: str = "INFO"
    debug: bool = True
    googlemaps_key: str = ""
    db_url: str = "sqlite:///storage/wedding.db"

    wedding_couple_contact: ContactInfo
    toast_master_contact: list[ContactInfo] = []

    date: WeddingDate | None = None
    venue: WeddingVenue | None = None
    faq: list[FaqEntry] = []

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


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return the application's cached configuration, loading it on first access.

    Returns:
        Config: The application's runtime configuration singleton.
    """
    return Config.load(CONFIG_FILE)
