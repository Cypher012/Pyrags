from typing import Literal

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata preserved for an indexed document chunk."""

    file_name: str | None = None
    file_type: Literal["pdf", "docx"] | None = None
    page_number: int | None = Field(default=None, ge=1)
    chunk_index: int | None = Field(default=None, ge=0)

    def as_pinecone_metadata(self) -> dict[str, str | int]:
        """Return only metadata types supported by Pinecone."""

        metadata: dict[str, str | int] = {}

        if self.file_name is not None:
            metadata["file_name"] = self.file_name
        if self.file_type is not None:
            metadata["file_type"] = self.file_type
        if self.page_number is not None:
            metadata["page_number"] = self.page_number
        if self.chunk_index is not None:
            metadata["chunk_index"] = self.chunk_index

        return metadata


class DocumentChunk(BaseModel):
    """A text chunk and the metadata attached before vectorization."""

    content: str = Field(min_length=1)
    metadata: DocumentMetadata


class SourceDocument(BaseModel):
    """A retrieved chunk returned to the API client as citation context."""

    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)

    @classmethod
    def from_langchain_document(cls, document: Document) -> "SourceDocument":
        """Convert a retrieved LangChain document to the public response model."""

        raw_metadata = document.metadata
        metadata = DocumentMetadata(
            file_name=_string_value(raw_metadata.get("file_name")),
            file_type=_file_type_value(raw_metadata.get("file_type")),
            page_number=_positive_int_value(raw_metadata.get("page_number")),
            chunk_index=_non_negative_int_value(raw_metadata.get("chunk_index")),
        )

        return cls(
            content=document.page_content,
            metadata=metadata,
        )


def _string_value(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _file_type_value(value: object) -> Literal["pdf", "docx"] | None:
    if value == "pdf":
        return "pdf"
    if value == "docx":
        return "docx"
    return None


def _positive_int_value(value: object) -> int | None:
    integer_value = _integer_value(value)
    return integer_value if integer_value is not None and integer_value >= 1 else None


def _non_negative_int_value(value: object) -> int | None:
    integer_value = _integer_value(value)
    return integer_value if integer_value is not None and integer_value >= 0 else None


def _integer_value(value: object) -> int | None:
    """Normalize integer metadata returned as either int or integer-valued float."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None
