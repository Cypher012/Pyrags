from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class UploadedDocument(BaseModel):
    job_id: UUID
    document_id: UUID
    filename: str


class BatchUploadResponse(BaseModel):
    conversation_id: UUID
    jobs: list[UploadedDocument]


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
    conversation_id: UUID | None = None
