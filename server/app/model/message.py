from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

from app.model.common import RoleEnum, Timestamp

if TYPE_CHECKING:
    from app.model.conversation import Conversation


class MessageBase(SQLModel):
    content: str
    role: RoleEnum


class Message(MessageBase, Timestamp, table=True):
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(
        foreign_key="conversations.id", nullable=False, ondelete="CASCADE"
    )
    source_documents: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(
            JSONB,
            nullable=False,
            server_default=text("'[]'::jsonb"),
        ),
    )
    conversation: "Conversation" = Relationship(back_populates="messages")


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: UUID
    conversation_id: UUID
