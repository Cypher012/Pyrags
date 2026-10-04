from typing import Literal
from uuid import UUID

from pydantic import BaseModel


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
