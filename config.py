"""
Configuration module for the Last Flight application.
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration class."""

    # API Configuration
    AIRLABS_API_KEY = os.getenv("AIRLABS_API_KEY", "")
    AIRPORT_ICAO = os.getenv("AIRPORT_ICAO", "KDAL")
    AIRLINES_FILTER = os.getenv("AIRLINES_FILTER", "WN,DL").split(",")
    FLIGHTS_LIMIT = int(os.getenv("FLIGHTS_LIMIT", "10"))

    # Email Configuration
    EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
    EMAIL_SENDER_PASSWORD = os.getenv("EMAIL_SENDER_PASSWORD", "")
    EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
    EMAIL_SMTP_SERVER = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "flights.log")

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        if not cls.AIRLABS_API_KEY:
            raise ValueError("AIRLABS_API_KEY environment variable is required")

        if cls.EMAIL_ENABLED:
            required_email_fields = [
                "EMAIL_SENDER",
                "EMAIL_SENDER_PASSWORD",
                "EMAIL_RECIPIENT",
            ]
            missing = [field for field in required_email_fields if not getattr(cls, field)]
            if missing:
                raise ValueError(
                    f"Email is enabled but missing configuration: {', '.join(missing)}"
                )

    def __repr__(self):
        return (
            f"Config(AIRPORT_ICAO={self.AIRPORT_ICAO}, "
            f"AIRLINES_FILTER={self.AIRLINES_FILTER}, "
            f"FLIGHTS_LIMIT={self.FLIGHTS_LIMIT}, "
            f"EMAIL_ENABLED={self.EMAIL_ENABLED})"
        )
