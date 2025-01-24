"""
This file loads environment variables and provides configuration
across the application (tokens, IDs, environment, etc.).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Your environment-based settings class.
    """
    WHATSAPP_ACCESS_TOKEN: str
    WHATSAPP_VERIFY_TOKEN: str
    WHATSAPP_BUSINESS_ID: str
    WHATSAPP_PHONE_NUMBER_ID: str
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

# Instantiate the settings
settings = Settings()