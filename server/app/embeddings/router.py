import asyncio
import json
import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from app.embeddings.processor import run_embeddings_job
from app.embeddings.schemas import JobProgress

router = APIRouter()

logger = logging.getLogger(__name__)

job_queues: dict[str, asyncio.Queue[JobProgress]] = {}


class UploadResponse(BaseModel):
    job_id: str
    filename: str


class FileUpload(BaseModel):
    job_id: str
    filename: str
    size: int | None
    content_type: str | None


@router.post("/upload-file", response_model=UploadResponse)
async def upload_file(
    file: Annotated[UploadFile, File(description="PDF or DOCX documents")],
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

    job_id = str(uuid4())

    job_queues[job_id] = asyncio.Queue()

    asyncio.create_task(
        run_embeddings_job(
            job_queues=job_queues, job_id=job_id, content=content, filename=filename
        )
    )

    return UploadResponse(job_id=job_id, filename=filename)


@router.get("/upload-status/{job_id}", response_class=EventSourceResponse)
async def upload_status(job_id: str):
    queue = job_queues.get(job_id)

    if queue is None:
        raise HTTPException(status_code=404, detail="Job not found")

    while True:
        payload = await queue.get()

        payload = {"job_id": job_id, **payload.model_dump()}

        logger.info("Sending SSE event: %s", json.dumps(payload))

        yield ServerSentEvent(data=payload)

        if payload["stage"] in {"completed", "error"}:
            break


# @router.post("/upload-file", response_model=FileUpload)
# async def upload_file(
#     file: Annotated[UploadFile, File(description="PDF or DOCX document")],
# ) -> FileUpload:
#     upload = {
#         "job_id": str(uuid4()),
#         "filename": file.filename,
#         "size": file.size,
#         "content_type": file.content_type,
#     }

#     logger.info(f"file uploaded {upload}")

#     return FileUpload.model_validate(upload)
