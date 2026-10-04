from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, Relationship, SQLModel

from app.model.common import Timestamp
from app.model.document import DocumentResponse

if TYPE_CHECKING:
    from app.model.document import Document
    from app.model.message import Message


class ConversationBase(SQLModel):
    user_id: str
    title: str


class Conversation(ConversationBase, Timestamp, table=True):
    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    documents: list["Document"] = Relationship(
        back_populates="conversation", cascade_delete=True
    )
    messages: list["Message"] = Relationship(
        back_populates="conversation", cascade_delete=True
    )


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class ConversationResponse(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ConversationHeader(BaseModel):
    id: UUID
    title: str
    document_count: int
    documents: list[DocumentResponse] = Field(default_factory=list)
