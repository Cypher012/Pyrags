from datetime import UTC, datetime
from enum import Enum

from sqlmodel import Field, SQLModel


class RoleEnum(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class Timestamp(SQLModel):
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
