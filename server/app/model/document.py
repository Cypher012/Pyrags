from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Literal
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel, String

from app.model.common import Timestamp

if TYPE_CHECKING:
    from app.model.conversation import Conversation
    from app.model.document_chunk import DocumentChunk


class DocumentStatus(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class DocumentBase(SQLModel):
    file_name: str
    file_type: Literal["pdf", "docx"] = Field(sa_type=String())
    status: DocumentStatus
    size_bytes: int | None = Field(default=None, ge=1)
    page_count: int | None = Field(default=None, ge=1)


class Document(DocumentBase, Timestamp, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    conversation_id: UUID = Field(
        foreign_key="conversations.id",
        ondelete="CASCADE",
        nullable=False,
    )

    conversation: "Conversation" = Relationship(back_populates="documents")
    document_chunks: list["DocumentChunk"] = Relationship(
        back_populates="document", cascade_delete=True
    )


class DocumentCreate(DocumentBase):
    conversation_id: UUID


class DocumentPreview(SQLModel):
    content: str
    page_number: int | None = None


class DocumentResponse(DocumentBase):
    id: UUID
    created_at: datetime
    preview: DocumentPreview | None = None
