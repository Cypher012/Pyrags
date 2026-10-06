from typing import Any, Literal
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.model.common import Timestamp

IngestionStage = Literal[
    "upload", "extracting", "chunking", "embedding", "storing", "completed", "error"
]


class IngestionJob(Timestamp, SQLModel, table=True):
    __tablename__ = "ingestion_jobs"
    __table_args__ = (
        CheckConstraint("progress BETWEEN 0 AND 100", name="ck_ingestion_job_progress"),
        CheckConstraint(
            "stage IN ('upload', 'extracting', 'chunking', 'embedding', "
            "'storing', 'completed', 'error')",
            name="ck_ingestion_job_stage",
        ),
    )
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: UUID = Field(
        foreign_key="documents.id", ondelete="CASCADE", nullable=False, unique=True
    )
    user_id: str = Field(index=True)
    source_parts: list[dict[str, Any]] = Field(sa_column=Column(JSONB, nullable=False))
    prepared_chunks: list[dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )
    stage: IngestionStage = Field(default="upload", sa_type=String(), nullable=False)
    message: str = Field(default="Waiting for processing", max_length=500)
    progress: int = Field(default=20, ge=0, le=100)
    dispatched_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
