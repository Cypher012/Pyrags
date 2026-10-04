from typing import Literal

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    file_name: str | None = None
    file_type: Literal["pdf", "docx"] | None = None
    page_number: int | None = Field(default=None, ge=1)
    chunk_index: int = Field(ge=0)


class PreparedChunk(BaseModel):
    """A text chunk before embedding and persistence."""

    content: str = Field(min_length=1)
    metadata: DocumentMetadata


class SourceDocument(BaseModel):
    """A retrieved chunk returned to the API client as citation context."""

    content: str
    metadata: DocumentMetadata

    @classmethod
    def from_langchain_document(cls, document: Document) -> "SourceDocument":
        raw_metadata = document.metadata

        metadata = DocumentMetadata(
            file_name=_string_value(raw_metadata.get("file_name")),
            file_type=_file_type_value(raw_metadata.get("file_type")),
            page_number=_positive_int_value(raw_metadata.get("page_number")),
            chunk_index=_required_non_negative_int(raw_metadata.get("chunk_index")),
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


def _required_non_negative_int(value: object) -> int:
    integer_value = _integer_value(value)

    if integer_value is None or integer_value < 0:
        raise ValueError("chunk_index must be a non-negative integer")

    return integer_value


def _integer_value(value: object) -> int | None:
    """Normalize integer metadata returned as either int or integer-valued float."""

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None
