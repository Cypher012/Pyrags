from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class ModelProvider(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"


class ChatModelConfig(BaseModel):
    """Validated configuration shared by supported chat model providers."""

    model: str | None = Field(default=None, min_length=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)

    @field_validator("model")
    @classmethod
    def reject_placeholder_model(cls, model: str | None) -> str | None:
        if model == "string":
            raise ValueError("Choose a real model name or omit model to use the default")
        return model
