from enum import StrEnum

from pydantic import BaseModel, Field


class ModelProvider(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ChatModelConfig(BaseModel):
    """Validated configuration shared by supported chat model providers."""

    model: str | None = Field(default=None, min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
