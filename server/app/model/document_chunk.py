from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Index, Relationship, SQLModel

if TYPE_CHECKING:
    from app.model.document import Document


class DocumentChunkBase(SQLModel):
    content: str
    page_number: int | None = None
    chunk_index: int


class DocumentChunk(DocumentChunkBase, table=True):
    __tablename__ = "document_chunks"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_document_chunks_document_id_chunk_index",
        ),
        Index(
            "ix_document_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(
        foreign_key="documents.id", ondelete="CASCADE", nullable=False
    )

    embedding: list[float] = Field(sa_type=VECTOR(1024), nullable=False)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )

    document: "Document" = Relationship(back_populates="document_chunks")


class DocumentChunkCreate(DocumentChunkBase):
    pass
