import ssl
from typing import Self

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    APP_ENV: str = Field(default="development")
    FRONTEND_URL: str = "http://localhost:5173"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ENABLE_MOCK_API: bool = False
    DEBUG: bool = False
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1)
    MOCK_UPLOAD_DELAY_SECONDS: float = Field(default=0.5, ge=0)
    MOCK_STATUS_DELAY_SECONDS: float = Field(default=1.5, ge=0)
    MOCK_CHAT_DELAY_SECONDS: float = Field(default=0.75, ge=0)
    LOCAL_DATABASE_URL: str = ""
    NEON_DATABASE_URL: str = ""
    INNGEST_EVENT_KEY: str = ""
    INNGEST_SIGNING_KEY: str = ""

    @model_validator(mode="after")
    def validate_database_url(self) -> Self:
        selected_name = (
            "NEON_DATABASE_URL"
            if self.APP_ENV == "production"
            else "LOCAL_DATABASE_URL"
        )
        selected_url = getattr(self, selected_name)
        if not selected_url.strip():
            raise ValueError(f"{selected_name} is required for APP_ENV={self.APP_ENV}")
        try:
            parsed_url = make_url(selected_url)
        except Exception:
            raise ValueError(
                f"{selected_name} must be a valid PostgreSQL URL"
            ) from None
        if parsed_url.drivername not in {
            "postgres",
            "postgresql",
            "postgresql+asyncpg",
        }:
            raise ValueError(f"{selected_name} must use PostgreSQL with asyncpg")
        return self

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        return f"{self.FRONTEND_URL.rstrip('/')}/api/auth/jwks"

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        selected_url = (
            self.NEON_DATABASE_URL
            if self.APP_ENV == "production"
            else self.LOCAL_DATABASE_URL
        )
        database_url = make_url(selected_url).set(drivername="postgresql+asyncpg")
        if self.APP_ENV == "production":
            database_url = database_url.difference_update_query(
                ["sslmode", "channel_binding", "ssl"]
            )
        return database_url.render_as_string(hide_password=False)

    @property
    def DATABASE_CONNECT_ARGS(self) -> dict[str, ssl.SSLContext]:
        if self.APP_ENV == "production":
            return {"ssl": ssl.create_default_context()}
        return {}

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


config = Settings()
