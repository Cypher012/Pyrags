from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = Field(min_length=1)
    FRONTEND_URL: str = "http://localhost:5173"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ENABLE_MOCK_API: bool = False
    DEBUG: bool = False
    MAX_UPLOAD_SIZE_MB: int = Field(default=10, ge=1)
    MOCK_UPLOAD_DELAY_SECONDS: float = Field(default=0.5, ge=0)
    MOCK_STATUS_DELAY_SECONDS: float = Field(default=1.5, ge=0)
    MOCK_CHAT_DELAY_SECONDS: float = Field(default=0.75, ge=0)

    @computed_field
    @property
    def JWKS_URL(self) -> str:
        return f"{self.FRONTEND_URL.rstrip('/')}/api/auth/jwks"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


config = Settings()
