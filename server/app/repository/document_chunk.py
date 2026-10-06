from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.model.document import Document, DocumentStatus
from app.model.document_chunk import DocumentChunk

type RetrievedChunk = tuple[DocumentChunk, Document]


async def create_document_chunks(
    session: AsyncSession, chunks: list[DocumentChunk]
) -> list[DocumentChunk]:
    session.add_all(chunks)

    await session.flush()

    return chunks


async def search_document_chunks(
    session: AsyncSession,
    conversation_id: UUID,
    query_embedding: list[float],
    limit: int = 5,
) -> list[RetrievedChunk]:
    cosine_distance = col(DocumentChunk.embedding).op("<=>")(query_embedding)

    stmt = (
        select(DocumentChunk, Document)
        .join(
            Document,
            col(DocumentChunk.document_id) == col(Document.id),
        )
        .where(
            col(Document.conversation_id) == conversation_id,
            col(Document.status) == DocumentStatus.READY,
        )
        .order_by(cosine_distance)
        .limit(limit)
    )

    result = await session.execute(stmt)

    return list(result.tuples().all())
