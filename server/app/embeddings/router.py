import asyncio
import json
import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from app.core.config import config
from app.core.database import CurrentUserDep
from app.embeddings.processor import run_embeddings_job
from app.embeddings.schemas import JobProgress

router = APIRouter()

logger = logging.getLogger(__name__)

job_queues: dict[str, asyncio.Queue[JobProgress]] = {}
job_owners: dict[str, str] = {}


def discard_job(job_id: str) -> None:
    job_queues.pop(job_id, None)
    job_owners.pop(job_id, None)


async def process_job(job_id: str, content: bytes, filename: str, user_id: str) -> None:
    try:
        await run_embeddings_job(
            job_queues=job_queues,
            job_id=job_id,
            content=content,
            filename=filename,
            user_id=user_id,
        )
    finally:
        asyncio.get_running_loop().call_later(300, discard_job, job_id)


class UploadResponse(BaseModel):
    job_id: str
    filename: str


@router.post("/upload-file", response_model=UploadResponse)
async def upload_file(
    file: Annotated[UploadFile, File(description="PDF or DOCX documents")],
    current_user: CurrentUserDep,
) -> UploadResponse:
    filename = file.filename

    if not filename:
        raise HTTPException(status_code=400, detail="A file is required")

    allowed_extensions = {".pdf", ".docx"}
    extension = "." + filename.rsplit(".", 1)[-1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX documents are supported"
        )

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")

    max_bytes = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Files must be smaller than {config.MAX_UPLOAD_SIZE_MB} MB",
        )

    job_id = str(uuid4())

    job_queues[job_id] = asyncio.Queue()
    job_owners[job_id] = current_user.id

    asyncio.create_task(
        process_job(
            job_id=job_id,
            content=content,
            filename=filename,
            user_id=current_user.id,
        )
    )

    return UploadResponse(job_id=job_id, filename=filename)


async def get_job_queue(
    job_id: str, current_user: CurrentUserDep
) -> asyncio.Queue[JobProgress]:
    queue = job_queues.get(job_id)

    if queue is None or job_owners.get(job_id) != current_user.id:
        raise HTTPException(status_code=404, detail="Job not found")

    return queue


@router.get("/upload-status/{job_id}", response_class=EventSourceResponse)
async def upload_status(
    job_id: str,
    queue: Annotated[asyncio.Queue[JobProgress], Depends(get_job_queue)],
):
    while True:
        payload = await queue.get()

        payload = {"job_id": job_id, **payload.model_dump(mode="json")}

        logger.info("Sending SSE event: %s", json.dumps(payload))

        yield ServerSentEvent(data=payload)

        if payload["stage"] in {"completed", "error"}:
            discard_job(job_id)
            break
