from collections.abc import AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_community.chat_message_histories import ChatMessageHistory

from app.chat.schemas import ChatRequest, ChatResponse, ChatServiceRequest
from app.chat.service import query_bot, stream_bot

router = APIRouter()

# Temporary in-memory session storage.
# Replace with Redis/database persistence later.
sessions: dict[str, ChatMessageHistory] = {}


@router.post("/query", response_model=ChatResponse)
async def query_chatbot(chat_request: ChatRequest) -> ChatResponse | StreamingResponse:
    """Handle a chat query with session-based conversation history."""

    try:
        session_id = chat_request.session_id or str(uuid4())
        chat_history = sessions.setdefault(session_id, ChatMessageHistory())
        service_request = ChatServiceRequest(
            message=chat_request.message,
            chat_history=chat_history.messages,
            model_provider=chat_request.model_provider,
            model_options=chat_request.model_options,
        )

        if chat_request.is_stream:

            async def generate() -> AsyncGenerator[str]:
                answer_parts: list[str] = []

                async for chunk in stream_bot(service_request):
                    answer_parts.append(chunk.token)
                    yield f"{chunk.model_dump_json()}\n"

                chat_history.add_user_message(chat_request.message)
                chat_history.add_ai_message("".join(answer_parts))

            return StreamingResponse(
                generate(),
                media_type="application/x-ndjson",
                headers={"X-Session-ID": session_id},
            )

        result = await query_bot(service_request)
        chat_history.add_user_message(chat_request.message)
        chat_history.add_ai_message(result.answer)

        return ChatResponse(
            session_id=session_id,
            response=result.answer,
            source_documents=result.source_documents,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing chat request: {exc}",
        ) from exc
