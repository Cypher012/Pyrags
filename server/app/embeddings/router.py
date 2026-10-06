import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel

from app.core.config import config
from app.core.database import CurrentUserDep
from app.embeddings.jobs import publish_job, read_job_progress, save_upload_jobs
from app.embeddings.schemas import BatchUploadResponse, JobProgress

router = APIRouter()
logger = logging.getLogger(__name__)


class UploadResponse(BaseModel):
    job_id: str
    filename: str


async def read_upload(file: UploadFile) -> tuple[bytes, str]:
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="A file is required")
    extension = "." + filename.rsplit(".", 1)[-1].lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(status_code=400, detail=f"{filename}: only PDF and DOCX are supported")
    limit = config.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    content = await file.read(limit)
    if not content:
        raise HTTPException(status_code=400, detail=f"{filename}: the uploaded file is empty")
    if len(content) >= limit:
        raise HTTPException(status_code=413, detail=f"{filename}: files must be smaller than {config.MAX_UPLOAD_SIZE_MB} MiB")
    return content, filename


async def save_and_dispatch(
    files: list[UploadFile], user_id: str
) -> BatchUploadResponse:
    if not 1 <= len(files) <= 3:
        raise HTTPException(status_code=400, detail="Select between one and three documents")
    contents = [await read_upload(file) for file in files]
    try:
        response = await save_upload_jobs(contents, user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    for document in response.jobs:
        try:
            await publish_job(str(document.job_id))
        except Exception:
            logger.exception("Event publishing failed for saved job %s", document.job_id)
    return response


@router.post("/upload-file", response_model=UploadResponse)
async def upload_file(
    file: Annotated[UploadFile, File(description="PDF or DOCX document")],
    current_user: CurrentUserDep,
) -> UploadResponse:
    response = await save_and_dispatch([file], current_user.id)
    document = response.jobs[0]
    return UploadResponse(job_id=str(document.job_id), filename=document.filename)


@router.post("/upload-files", response_model=BatchUploadResponse)
async def upload_files(
    files: Annotated[list[UploadFile], File(description="One to three PDF or DOCX documents")],
    current_user: CurrentUserDep,
) -> BatchUploadResponse:
    return await save_and_dispatch(files, current_user.id)


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
