import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from inngest import Event, NonRetriableError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.core.database import async_session
from app.core.inngest import inngest_clent
from app.embeddings.documents import PreparedChunk
from app.embeddings.processor import (
    FileType,
    SourcePart,
    chunk_document,
    extract_document,
    extract_docx_page_count,
)
from app.embeddings.schemas import BatchUploadResponse, JobProgress, UploadedDocument
from app.embeddings.service import generate_embeddings
from app.embeddings.titles import generate_conversation_title
from app.model.conversation import Conversation, ConversationCreate
from app.model.document import Document, DocumentCreate, DocumentStatus
from app.model.document_chunk import DocumentChunk
from app.model.ingestion_job import IngestionJob, IngestionStage
from app.repository.conversation import create_conversation
from app.repository.document import create_document, update_document_status

BATCH_SIZE = 32
MAX_SOURCE_CHARACTERS = 2_000_000
MAX_CHUNKS = 16_000
logger = logging.getLogger(__name__)


def _set_progress(
    job: IngestionJob, stage: IngestionStage, message: str, progress: int
) -> None:
    job.stage = stage
    job.message = message
    job.progress = max(job.progress, min(100, max(0, progress)))
    job.updated_at = datetime.now(UTC)


async def _get_job(
    session: AsyncSession, job_id: str, lock: bool = False
) -> IngestionJob:
    statement = select(IngestionJob).where(col(IngestionJob.id) == UUID(job_id))
    if lock:
        statement = statement.with_for_update()
    result = await session.execute(statement)
    job = result.scalar_one_or_none()
    if job is None:
        raise NonRetriableError("Ingestion job no longer exists")
    return job


def _manifest(job: IngestionJob) -> dict[str, int]:
    count = len(job.prepared_chunks)
    return {
        "chunk_count": count,
        "batch_count": (count + BATCH_SIZE - 1) // BATCH_SIZE,
    }


async def _stored_indexes(session: AsyncSession, document_id: UUID) -> set[int]:
    result = await session.execute(
        select(col(DocumentChunk.chunk_index)).where(
            col(DocumentChunk.document_id) == document_id
        )
    )
    return set(result.scalars().all())


async def extract_upload(
    content: bytes, filename: str
) -> tuple[FileType, list[SourcePart], int | None]:
    try:
        file_type, source_parts = await asyncio.to_thread(
            extract_document, content, filename
        )
        page_count = (
            len(source_parts)
            if file_type == "pdf"
            else await asyncio.to_thread(extract_docx_page_count, content)
        )
    except Exception as exc:
        raise ValueError(f"{filename}: the document could not be read") from exc

    if not any(text.strip() for _, text in source_parts):
        raise ValueError(f"{filename}: no text could be extracted")
    if sum(len(text) for _, text in source_parts) > MAX_SOURCE_CHARACTERS:
        raise ValueError(f"{filename}: the extracted document text is too large")
    return file_type, source_parts, page_count


async def save_upload_jobs(
    files: list[tuple[bytes, str]], user_id: str
) -> BatchUploadResponse:
    if not 1 <= len(files) <= 3:
        raise ValueError("Select between one and three documents")
    extracted = [await extract_upload(content, filename) for content, filename in files]
    title = Path(files[0][1]).stem
    if len(files) > 1:
        extra = len(files) - 1
        title += f" + {extra} document{'s' if extra > 1 else ''}"

    async with async_session() as session, session.begin():
        conversation = await create_conversation(
            session, ConversationCreate(user_id=user_id, title=title)
        )
        uploaded: list[UploadedDocument] = []
        for (content, filename), (file_type, source_parts, page_count) in zip(
            files, extracted, strict=True
        ):
            document = await create_document(
                session,
                DocumentCreate(
                    conversation_id=conversation.id,
                    file_name=filename,
                    file_type=file_type,
                    status=DocumentStatus.PROCESSING,
                    size_bytes=len(content),
                    page_count=page_count,
                ),
            )
            job = IngestionJob(
                document_id=document.id,
                user_id=user_id,
                source_parts=[
                    {"page_number": page_number, "text": text}
                    for page_number, text in source_parts
                ],
            )
            session.add(job)
            await session.flush()
            uploaded.append(UploadedDocument(
                job_id=job.id, document_id=document.id, filename=filename
            ))
        response = BatchUploadResponse(conversation_id=conversation.id, jobs=uploaded)
    return response


async def save_upload_job(content: bytes, filename: str, user_id: str) -> UUID:
    response = await save_upload_jobs([(content, filename)], user_id)
    return response.jobs[0].job_id


async def prepare_chunks(job_id: str) -> dict[str, int]:
    async with async_session() as session:
        job = await _get_job(session, job_id)
        if job.stage == "error":
            raise NonRetriableError("Ingestion job has already failed")
        if job.prepared_chunks:
            return _manifest(job)
        document = await session.get(Document, job.document_id)
        if document is None:
            raise NonRetriableError("Document no longer exists")
        source_parts = [
            (part["page_number"], part["text"]) for part in job.source_parts
        ]
        filename, file_type = document.file_name, document.file_type

    prepared = await asyncio.to_thread(
        chunk_document, source_parts, filename, file_type
    )
    if not prepared or len(prepared) > MAX_CHUNKS:
        raise NonRetriableError("Document has no chunks or exceeds the chunk limit")

    async with async_session() as session, session.begin():
        job = await _get_job(session, job_id, lock=True)
        if job.stage == "error":
            raise NonRetriableError("Ingestion job has already failed")
        if not job.prepared_chunks:
            job.prepared_chunks = [item.model_dump(mode="json") for item in prepared]
            _set_progress(job, "chunking", "Document prepared for embedding", 50)
            session.add(job)
        return _manifest(job)


async def embed_and_store_batch(job_id: str, batch_index: int) -> dict[str, int]:
    async with async_session() as session, session.begin():
        job = await _get_job(session, job_id, lock=True)
        if job.stage == "error":
            raise NonRetriableError("Ingestion job has already failed")
        if batch_index < 0 or batch_index >= _manifest(job)["batch_count"]:
            raise NonRetriableError("Invalid embedding batch index")
        start = batch_index * BATCH_SIZE
        batch = [
            PreparedChunk.model_validate(item)
            for item in job.prepared_chunks[start : start + BATCH_SIZE]
        ]
        expected = {item.metadata.chunk_index for item in batch}
        if expected <= await _stored_indexes(session, job.document_id):
            return {"stored": len(batch)}
        document_id = job.document_id
        _set_progress(job, "embedding", "Generating embeddings", 70)
        session.add(job)

    embedded = await asyncio.to_thread(generate_embeddings, batch)
    if len(embedded) != len(batch) or any(
        len(item.embedding) != 1024 for item in embedded
    ):
        raise ValueError("The embedding response has unexpected dimensions")

    async with async_session() as session, session.begin():
        job = await _get_job(session, job_id, lock=True)
        if job.stage == "error":
            raise NonRetriableError("Ingestion job has already failed")
        if job.stage == "completed":
            return {"stored": len(batch)}
        rows = [
            DocumentChunk(
                document_id=document_id,
                content=item.content,
                page_number=item.metadata.page_number,
                chunk_index=item.metadata.chunk_index,
                embedding=item.embedding,
            ).model_dump()
            for item in embedded
        ]
        await session.execute(
            insert(DocumentChunk)
            .values(rows)
            .on_conflict_do_nothing(
                constraint="uq_document_chunks_document_id_chunk_index"
            )
        )
        stored = await _stored_indexes(session, document_id)
        if not expected <= stored:
            raise RuntimeError("The embedding batch was not completely stored")
        progress = 70 + int(29 * len(stored) / len(job.prepared_chunks))
        _set_progress(job, "storing", "Storing document vectors", min(99, progress))
        session.add(job)
    return {"stored": len(batch)}


async def finish_job(job_id: str) -> dict[str, str]:
    async with async_session() as session, session.begin():
        job = await _get_job(session, job_id, lock=True)
        document = await session.get(Document, job.document_id)
        if document is None:
            raise NonRetriableError("Document no longer exists")
        if job.stage == "error":
            raise NonRetriableError("Ingestion job has already failed")
        expected = set(range(len(job.prepared_chunks)))
        if not expected or expected != await _stored_indexes(session, document.id):
            raise RuntimeError("The document is not completely indexed")
        result = await session.execute(
            select(Conversation)
            .where(col(Conversation.id) == document.conversation_id)
            .with_for_update()
        )
        conversation = result.scalar_one()
        already_completed = job.stage == "completed"
        await update_document_status(session, document, DocumentStatus.READY)
        await session.flush()
        result = await session.execute(
            select(Document)
            .where(col(Document.conversation_id) == conversation.id)
            .order_by(col(Document.created_at), col(Document.id))
        )
        documents = list(result.scalars().all())
        initial_title = Path(documents[0].file_name).stem
        if len(documents) > 1:
            extra = len(documents) - 1
            initial_title += f" + {extra} document{'s' if extra > 1 else ''}"
        if (
            not already_completed
            and conversation.title == initial_title
            and all(item.status == DocumentStatus.READY for item in documents)
        ):
            title = await generate_conversation_title(session, documents)
            if title:
                conversation.title = title
                conversation.updated_at = datetime.now(UTC)
                session.add(conversation)
        _set_progress(job, "completed", "Document processing completed", 100)
        session.add(job)
        return {
            "job_id": str(job.id),
            "conversation_id": str(document.conversation_id),
        }


async def mark_failed(job_id: str) -> None:
    async with async_session() as session, session.begin():
        result = await session.execute(
            select(IngestionJob)
            .where(col(IngestionJob.id) == UUID(job_id))
            .with_for_update()
        )
        job = result.scalar_one_or_none()
        if job is None or job.stage == "completed":
            return
        document = await session.get(Document, job.document_id)
        if document is None or document.status == DocumentStatus.READY:
            return
        await update_document_status(session, document, DocumentStatus.FAILED)
        _set_progress(
            job,
            "error",
            "Document processing failed. Please try a new upload.",
            job.progress,
        )
        session.add(job)


async def read_job_progress(job_id: str, user_id: str) -> JobProgress:
    try:
        identifier = UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found") from None
    async with async_session() as session:
        result = await session.execute(
            select(IngestionJob, Document)
            .join(Document, col(Document.id) == col(IngestionJob.document_id))
            .join(Conversation, col(Conversation.id) == col(Document.conversation_id))
            .where(
                col(IngestionJob.id) == identifier,
                col(IngestionJob.user_id) == user_id,
                col(Conversation.user_id) == user_id,
            )
        )
        row = result.one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Job not found")
        job, document = row
        return JobProgress(
            stage=job.stage,
            message=job.message,
            progress=job.progress,
            conversation_id=(
                document.conversation_id if job.stage == "completed" else None
            ),
        )


async def require_ready_document(session: AsyncSession, conversation_id: UUID) -> None:
    result = await session.execute(
        select(col(Document.status)).where(
            col(Document.conversation_id) == conversation_id
        )
    )
    statuses = list(result.scalars().all())
    if not statuses or any(status != DocumentStatus.READY for status in statuses):
        raise HTTPException(
            status_code=409,
            detail="All documents must be ready before asking a question.",
        )


async def publish_job(job_id: str) -> None:
    await inngest_clent.send(
        Event(
            name="pyrags/document.uploaded",
            id=f"document-uploaded-{job_id}",
            data={"job_id": job_id},
        )
    )
    async with async_session() as session, session.begin():
        job = await session.get(IngestionJob, UUID(job_id))
        if job is not None and job.dispatched_at is None:
            job.dispatched_at = datetime.now(UTC)
            job.updated_at = datetime.now(UTC)
            session.add(job)


async def dispatch_pending_jobs() -> dict[str, int]:
    async with async_session() as session:
        result = await session.execute(
            select(col(IngestionJob.id))
            .where(
                col(IngestionJob.dispatched_at).is_(None),
                col(IngestionJob.stage).not_in(["completed", "error"]),
            )
            .order_by(col(IngestionJob.created_at))
            .limit(20)
        )
        job_ids = list(result.scalars().all())
    sent = 0
    for job_id in job_ids:
        try:
            await publish_job(str(job_id))
            sent += 1
        except Exception:
            logger.exception("Could not dispatch saved ingestion job %s", job_id)
    return {"sent": sent, "pending": len(job_ids) - sent}
