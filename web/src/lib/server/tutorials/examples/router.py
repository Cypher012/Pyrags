import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Annotated

import inngest
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from app.core.config import config
from app.core.database import CurrentUserDep
from app.core.inngest import inngest_client
from app.embeddings.jobs import read_job_progress, save_upload_job
from app.embeddings.schemas import JobProgress

router = APIRouter()
logger = logging.getLogger(__name__)


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
    extension = "." + filename.rsplit(".", 1)[-1].lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(content) > config.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="The uploaded file is too large")
    try:
        job_id = await save_upload_job(content, filename, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        await inngest_client.send(
            inngest.Event(
                name="pyrags/document.uploaded",
                id=f"document-uploaded-{job_id}",
                data={"job_id": str(job_id)},
            )
        )
    except Exception as exc:
        logger.exception("Event publishing failed for saved job %s", job_id)
        raise HTTPException(
            status_code=503,
            detail="The document was saved but processing could not be started.",
        ) from exc
    return UploadResponse(job_id=str(job_id), filename=filename)


async def get_owned_job_progress(
    job_id: str, current_user: CurrentUserDep
) -> JobProgress:
    return await read_job_progress(job_id, current_user.id)


@router.get("/upload-status/{job_id}", response_class=EventSourceResponse)
async def upload_status(
    job_id: str,
    request: Request,
    current_user: CurrentUserDep,
    initial: Annotated[JobProgress, Depends(get_owned_job_progress)],
) -> AsyncIterator[ServerSentEvent]:
    snapshot = initial
    previous: dict | None = None
    while not await request.is_disconnected():
        payload = {"job_id": job_id, **snapshot.model_dump(mode="json")}
        if payload != previous:
            yield ServerSentEvent(data=payload)
            previous = payload
        if snapshot.stage in {"completed", "error"}:
            return
        await asyncio.sleep(1)
        try:
            snapshot = await read_job_progress(job_id, current_user.id)
        except HTTPException as exc:
            if exc.status_code == 404:
                return
            raise
