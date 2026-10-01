from typing import Literal

from pydantic import BaseModel, Field


class JobProgress(BaseModel):
    stage: Literal[
        "upload",
        "extracting",
        "chunking",
        "embedding",
        "storing",
        "completed",
        "error",
    ]
    message: str
    progress: int


class EmbeddingResponse(BaseModel):
    """Result returned after processing and indexing an uploaded document."""

    status: Literal["success", "error"]
    message: str
    chunk_count: int = Field(ge=0)
