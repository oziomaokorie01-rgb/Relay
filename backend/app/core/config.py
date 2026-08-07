from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration for Relay.

    Values are loaded from environment variables and an optional
    `.env` file.
    """

    app_env: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    app_name: str = "Relay"
    api_prefix: str = "/api/v1"

    database_url: str = (
        "sqlite+aiosqlite:///./relay.db"
    )

    cors_origins: str = (
        "http://localhost:5173"
    )

    llm_api_key: str | None = None
    llm_model: str | None = None

    llm_timeout_seconds: int = Field(
        default=60,
        ge=1,
    )

    # DataHub configuration
    datahub_provider: Literal[
        "mock",
        "graphql",
    ] = "mock"

    datahub_base_url: str | None = None
    datahub_token: str | None = None

    datahub_timeout_seconds: float = Field(
        default=20.0,
        gt=0,
    )

    datahub_writeback_enabled: bool = False

    review_minimum_confidence: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
    )

    memory_inheritance_threshold: float = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
    )

    human_approval_required: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Return one cached Settings instance for the
    application process.
    """

    return Settings()