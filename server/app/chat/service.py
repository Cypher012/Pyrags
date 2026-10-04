import asyncio
from collections.abc import AsyncGenerator
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat.model import ChatModelConfig
from app.chat.model_factory import ModelFactory
from app.chat.prompts import HISTORY_PROMPT, SYSTEM_PROMPT
from app.chat.schemas import (
    ChatRequest,
    ChatServiceRequest,
    ChatServiceResponse,
    ChatStreamChunk,
    ChatStreamComplete,
)
from app.embeddings.documents import DocumentMetadata, SourceDocument
from app.embeddings.service import generate_query_embedding
from app.model.message import Message
from app.repository.document_chunk import RetrievedChunk, search_document_chunks


def _to_langchain_message(messages: list[Message]) -> list[BaseMessage]:
    """Convert persisted chat messages into LangChain messages."""

    chat_history: list[BaseMessage] = []

    for message in messages:
        match message.role:
            case "user":
                chat_history.append(HumanMessage(content=message.content))
            case "assistant":
                chat_history.append(AIMessage(content=message.content))
            case _:
                chat_history.append(SystemMessage(content=message.content))

    return chat_history


def create_chat_service_request(
    chat_request: ChatRequest,
    messages: list[Message],
) -> ChatServiceRequest:
    """Build the request consumed by the RAG service."""
    return ChatServiceRequest(
        message=chat_request.message,
        chat_history=_to_langchain_message(messages),
        model_provider=chat_request.model_provider,
        model_options=chat_request.model_options,
    )


def create_chat_prompt() -> ChatPromptTemplate:
    """Prompt used to generate the final answer."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Context: \n{context}\n\nQuestion: \n{input}"),
        ]
    )


def _build_context(chunks: list[RetrievedChunk]) -> str:
    """Convert retrieved database chunks into a prompt context."""

    return "\n\n".join(
        (
            f"[Source: {document.file_name}"
            f"{f', page {chunk.page_number}' if chunk.page_number else ''}]\n"
            f"{chunk.content}"
        )
        for chunk, document in chunks
    )


def _build_source_documents(chunks: list[RetrievedChunk]) -> list[SourceDocument]:
    """Convert database chunks into API citation models."""

    return [
        SourceDocument(
            content=chunk.content,
            metadata=DocumentMetadata(
                file_name=document.file_name,
                file_type=document.file_type,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
            ),
        )
        for chunk, document in chunks
    ]


async def _retrieve_chunks(
    session: AsyncSession,
    conversation_id: UUID,
    request: ChatServiceRequest,
    model: BaseChatModel,
) -> list[RetrievedChunk]:
    search_query = request.message
    if request.chat_history:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", HISTORY_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )
        rewritten_query = await (prompt | model | StrOutputParser()).ainvoke(
            {"input": request.message, "chat_history": request.chat_history}
        )
        search_query = rewritten_query.strip() or request.message

    query_embedding = await asyncio.to_thread(generate_query_embedding, search_query)
    return await search_document_chunks(
        session, conversation_id, query_embedding, limit=5
    )


async def query_bot(
    session: AsyncSession,
    conversation_id: UUID,
    request: ChatServiceRequest,
) -> ChatServiceResponse:
    """Run a non-streaming RAG query using pgvector retrieval."""

    model_options = request.model_options or ChatModelConfig()

    model = ModelFactory().get_chat_model(
        provider=request.model_provider,
        model_options=model_options,
    )

    chunks = await _retrieve_chunks(session, conversation_id, request, model)
    context = _build_context(chunks)

    chain = create_chat_prompt() | model | StrOutputParser()

    answer = await chain.ainvoke(
        {
            "input": request.message,
            "context": context,
            "chat_history": request.chat_history,
        }
    )

    return ChatServiceResponse(
        answer=answer, source_documents=_build_source_documents(chunks)
    )


async def stream_bot(
    session: AsyncSession,
    conversation_id: UUID,
    request: ChatServiceRequest,
) -> AsyncGenerator[ChatStreamChunk | ChatStreamComplete]:
    """Stream a RAG response using pgvector retrieval.

    Yields token chunks followed by one final ChatStreamComplete event that
    carries the full answer and its source documents.
    """

    model_options = request.model_options or ChatModelConfig()

    model = ModelFactory().get_chat_model(
        provider=request.model_provider,
        model_options=model_options,
    )

    chunks = await _retrieve_chunks(session, conversation_id, request, model)
    context = _build_context(chunks)

    chain = create_chat_prompt() | model | StrOutputParser()

    answer_parts: list[str] = []

    async for token in chain.astream(
        {
            "input": request.message,
            "context": context,
            "chat_history": request.chat_history,
        }
    ):
        if token:
            answer_parts.append(token)
            yield ChatStreamChunk(token=token)

    yield ChatStreamComplete(
        conversation_id=conversation_id,
        response="".join(answer_parts),
        source_documents=_build_source_documents(chunks),
    )
