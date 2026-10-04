from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.model.document import Document, DocumentCreate, DocumentStatus


async def create_document(session: AsyncSession, data: DocumentCreate) -> Document:
    document = Document.model_validate(data)

    session.add(document)
    await session.flush()

    return document


async def update_document_status(
    session: AsyncSession, document: Document, status: DocumentStatus
) -> Document:
    document.status = status
    document.updated_at = datetime.now(UTC)

    session.add(document)
    await session.flush()

    return document
