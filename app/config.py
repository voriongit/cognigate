"""
Application configuration using Pydantic Settings.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Cognigate Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # API
    api_prefix: str = "/v1"
    api_key_header: str = "X-API-Key"

    # Security
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    access_token_expire_minutes: int = 30

    # Trust Engine
    default_trust_level: int = 1
    trust_decay_rate: float = 0.01

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # External Services (future)
    # database_url: str = ""
    # redis_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
