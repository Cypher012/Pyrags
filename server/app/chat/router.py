from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from app.chat.schemas import ChatRequest, ChatResponse, ChatStreamComplete
from app.chat.service import (
    create_chat_service_request,
    query_bot,
    stream_bot,
)
from app.chat.usage import get_query_usage, refund_query, reserve_query
from app.core.database import CurrentUserDep, SessionDep
from app.embeddings.jobs import require_ready_document
from app.model.conversation import Conversation, ConversationHeader, ConversationUpdate
from app.model.message import Message, RoleEnum
from app.model.query_usage import QueryUsageResponse
from app.repository.conversation import (
    delete_conversation_for_user,
    get_conversation_for_user,
    get_conversation_header,
    list_conversations_for_user,
    rename_conversation_for_user,
)
from app.repository.message import (
    create_message,
    get_messages_for_conversation,
)

router = APIRouter()


@router.post(
    "/conversations/{conversation_id}/query",
    response_model=ChatResponse,
)
async def query_chatbot(
    conversation_id: UUID,
    chat_request: ChatRequest,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ChatResponse | StreamingResponse:
    """Send a message to an existing conversation."""

    conversation = await get_conversation_for_user(
        session=session,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    await require_ready_document(session, conversation_id)

    messages = await get_messages_for_conversation(
        session=session,
        conversation_id=conversation_id,
    )

    service_request = create_chat_service_request(
        chat_request=chat_request,
        messages=messages,
    )
    query_day = await reserve_query(session, current_user)

    if chat_request.is_stream:

        async def generate() -> AsyncGenerator[str]:
            answer = ""
            source_documents = []
            completed = False

            try:
                await create_message(
                    session=session,
                    conversation_id=conversation_id,
                    role=RoleEnum.USER,
                    content=chat_request.message,
                )

                async for event in stream_bot(
                    session=session,
                    conversation_id=conversation_id,
                    request=service_request,
                ):
                    if isinstance(event, ChatStreamComplete):
                        answer = event.response
                        source_documents = event.source_documents
                        continue

                    yield f"{event.model_dump_json()}\n"

                await create_message(
                    session=session,
                    conversation_id=conversation_id,
                    role=RoleEnum.ASSISTANT,
                    content=answer,
                    source_documents=[
                        source.model_dump(mode="json") for source in source_documents
                    ],
                )

                await session.commit()
                completed = True

                completion = ChatStreamComplete(
                    conversation_id=conversation_id,
                    response=answer,
                    source_documents=source_documents,
                )

                yield f"{completion.model_dump_json()}\n"

            except BaseException:
                await session.rollback()
                if not completed:
                    await refund_query(session, current_user, query_day)
                raise

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
        )

    try:
        await create_message(
            session=session,
            conversation_id=conversation_id,
            role=RoleEnum.USER,
            content=chat_request.message,
        )

        result = await query_bot(
            session=session,
            conversation_id=conversation_id,
            request=service_request,
        )

        await create_message(
            session=session,
            conversation_id=conversation_id,
            role=RoleEnum.ASSISTANT,
            content=result.answer,
            source_documents=[
                source.model_dump(mode="json") for source in result.source_documents
            ],
        )

        await session.commit()

    except Exception as exc:
        await session.rollback()
        await refund_query(session, current_user, query_day)

        raise HTTPException(
            status_code=500,
            detail="Error processing chat request",
        ) from exc
    except BaseException:
        await session.rollback()
        await refund_query(session, current_user, query_day)
        raise

    return ChatResponse(
        conversation_id=conversation_id,
        response=result.answer,
        source_documents=result.source_documents,
    )


@router.get("/usage", response_model=QueryUsageResponse)
async def get_daily_query_usage(
    session: SessionDep, current_user: CurrentUserDep
) -> QueryUsageResponse:
    return await get_query_usage(session, current_user)


@router.get("/conversations", response_model=list[Conversation])
async def get_user_conversations(
    session: SessionDep,
    current_user: CurrentUserDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
):
    conversations = await list_conversations_for_user(session, current_user.id, limit)

    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationHeader)
async def get_conversation(
    conversation_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> ConversationHeader:
    conversation = await get_conversation_header(
        session=session,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=list[Message])
async def get_user_messages_for_conversation(
    session: SessionDep, current_user: CurrentUserDep, conversation_id: UUID
):
    conversation = await get_conversation_for_user(
        session, conversation_id, current_user.id
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await get_messages_for_conversation(session, conversation.id)

    return messages


@router.patch("/conversations/{conversation_id}", response_model=Conversation)
async def rename_conversation(
    conversation_id: UUID,
    update: ConversationUpdate,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Conversation:
    conversation = await rename_conversation_for_user(
        session, conversation_id, current_user.id, update.title
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await session.commit()
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    session: SessionDep,
    current_user: CurrentUserDep,
) -> Response:
    deleted = await delete_conversation_for_user(session, conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await session.commit()
    return Response(status_code=204)
