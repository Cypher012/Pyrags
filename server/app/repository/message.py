from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlmodel import col, select

from app.model.common import RoleEnum
from app.model.conversation import Conversation
from app.model.message import Message


async def create_message(
    session: AsyncSession,
    conversation_id: UUID,
    role: RoleEnum,
    content: str,
    source_documents: list[dict[str, Any]] | None = None,
) -> Message:
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        source_documents=source_documents or [],
    )

    session.add(message)

    # Keep the parent's updated_at current so conversation lists sort by recency.
    conversation = await session.get(Conversation, conversation_id)
    if conversation is not None:
        conversation.updated_at = datetime.now(UTC)
        session.add(conversation)

    await session.flush()

    return message


async def get_messages_for_conversation(
    session: AsyncSession, conversation_id: UUID
) -> list[Message]:
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(col(Message.created_at))
    )

    result = await session.execute(stmt)

    return list(result.scalars())
