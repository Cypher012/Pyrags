from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, func, select

from app.model.conversation import Conversation, ConversationCreate, ConversationHeader
from app.model.document import Document, DocumentPreview, DocumentResponse
from app.model.document_chunk import DocumentChunk


async def create_conversation(
    session: AsyncSession, data: ConversationCreate
) -> Conversation:
    conversation = Conversation.model_validate(data)
    session.add(conversation)
    await session.flush()
    return conversation


async def get_conversation_for_user(
    session: AsyncSession, conversation_id: UUID, user_id: str
) -> Conversation | None:
    stmt = select(Conversation).where(
        Conversation.id == conversation_id, Conversation.user_id == user_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_conversations_for_user(
    session: AsyncSession, user_id: str, limit: int = 10
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(col(Conversation.updated_at).desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def rename_conversation_for_user(
    session: AsyncSession, conversation_id: UUID, user_id: str, title: str
) -> Conversation | None:
    conversation = await get_conversation_for_user(session, conversation_id, user_id)
    if conversation is None:
        return None
    conversation.title = title
    conversation.updated_at = datetime.now(UTC)
    session.add(conversation)
    await session.flush()
    return conversation


async def delete_conversation_for_user(
    session: AsyncSession, conversation_id: UUID, user_id: str
) -> bool:
    result = await session.execute(
        delete(Conversation)
        .where(col(Conversation.id) == conversation_id, col(Conversation.user_id) == user_id)
        .returning(Conversation.id)
    )
    return result.scalar_one_or_none() is not None


async def get_conversation_header(
    session: AsyncSession,
    conversation_id: UUID,
    user_id: str,
) -> ConversationHeader | None:
    stmt = (
        select(
            Conversation.id,
            Conversation.title,
            func.count(col(Document.id)).label("document_count"),
        )
        .outerjoin(Document, col(Document.conversation_id) == col(Conversation.id))
        .where(
            col(Conversation.id) == conversation_id,
            col(Conversation.user_id) == user_id,
        )
        .group_by(col(Conversation.id), col(Conversation.title))
    )
    result = await session.execute(stmt)
    row = result.mappings().one_or_none()

    if row is None:
        return None

    document_result = await session.execute(
        select(Document)
        .where(col(Document.conversation_id) == conversation_id)
        .order_by(col(Document.created_at), col(Document.id))
    )
    documents = document_result.scalars().all()
    previews = {}
    if documents:
        preview_result = await session.execute(
            select(
                DocumentChunk.document_id,
                DocumentChunk.content,
                DocumentChunk.page_number,
            )
            .where(col(DocumentChunk.document_id).in_([document.id for document in documents]))
            .distinct(col(DocumentChunk.document_id))
            .order_by(col(DocumentChunk.document_id), col(DocumentChunk.chunk_index))
        )
        previews = {
            document_id: DocumentPreview(content=content, page_number=page_number)
            for document_id, content, page_number in preview_result.all()
        }

    return ConversationHeader(
        id=row["id"],
        title=row["title"],
        document_count=row["document_count"],
        documents=[
            DocumentResponse.model_validate(document).model_copy(
                update={"preview": previews.get(document.id)}
            )
            for document in documents
        ],
    )
