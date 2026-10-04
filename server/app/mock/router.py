import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col, select

from app.chat.model_factory import ModelFactory
from app.chat.schemas import ChatRequest, ChatResponse, ChatStreamChunk
from app.chat.usage import refund_query, reserve_query
from app.core.config import config
from app.core.database import CurrentUserDep, SessionDep
from app.embeddings.documents import DocumentMetadata, SourceDocument
from app.embeddings.router import UploadResponse
from app.embeddings.schemas import JobProgress
from app.model.common import RoleEnum
from app.model.conversation import Conversation, ConversationHeader
from app.model.message import Message
from app.mock.data import (
    SAMPLE_BASE_TIME,
    SAMPLE_DOCUMENT_COUNTS,
    SAMPLE_FILES,
    SAMPLE_MESSAGES,
    SAMPLE_SOURCE_CONTENT,
)
from app.repository.message import create_message, get_messages_for_conversation

router = APIRouter()

FileType = Literal["pdf", "docx"]
uploads: dict[str, tuple[UUID, str, FileType]] = {}
job_queues: dict[str, asyncio.Queue[JobProgress]] = {}
conversations: dict[UUID, Conversation] = {}
conversation_files: dict[UUID, tuple[str, FileType]] = {}
document_counts: dict[UUID, int] = {}


class MockChatStreamComplete(ChatStreamChunk):
    conversation_id: UUID
    response: str
    source_documents: list[SourceDocument]


class MockMessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    role: RoleEnum
    content: str
    created_at: datetime
    updated_at: datetime
    source_documents: list[SourceDocument]


def mock_source_documents(conversation_id: UUID) -> list[SourceDocument]:
    filename, file_type = conversation_files.get(
        conversation_id, ("mock-source.pdf", "pdf")
    )
    return [
        SourceDocument(
            content=SAMPLE_SOURCE_CONTENT,
            metadata=DocumentMetadata(
                file_name=filename,
                file_type=file_type,
                page_number=1 if file_type == "pdf" else None,
                chunk_index=0,
            ),
        )
    ]


def seed_conversations() -> None:
    for index, filename in enumerate(SAMPLE_FILES):
        conversation_id = uuid5(NAMESPACE_URL, f"pyrags/mock/conversation/{index}")
        created_at = SAMPLE_BASE_TIME - timedelta(days=index)
        title = Path(filename).stem
        file_type: FileType = "docx" if filename.endswith(".docx") else "pdf"
        conversations[conversation_id] = Conversation(
            id=conversation_id,
            user_id="mock-user",
            title=title,
            created_at=created_at,
            updated_at=created_at,
        )
        conversation_files[conversation_id] = (filename, file_type)
        document_counts[conversation_id] = SAMPLE_DOCUMENT_COUNTS[index]


seed_conversations()


async def seed_mock_data(session: AsyncSession) -> None:
    seeded_ids = list(conversations)[: len(SAMPLE_FILES)]
    existing_conversations = set(
        (await session.execute(select(Conversation.id).where(col(Conversation.id).in_(seeded_ids))))
        .scalars()
        .all()
    )
    existing_messages = set(
        (await session.execute(select(Message.id).where(col(Message.conversation_id).in_(seeded_ids))))
        .scalars()
        .all()
    )

    conversation_rows = []
    message_rows = []
    for conversation_id in seeded_ids:
        conversation = conversations[conversation_id]
        if conversation_id not in existing_conversations:
            conversation_rows.append(conversation.model_dump())
        for index, (role, content) in enumerate(SAMPLE_MESSAGES):
            message_id = uuid5(
                NAMESPACE_URL, f"pyrags/mock/message/{conversation_id}/{index}"
            )
            if message_id not in existing_messages:
                created_at = conversation.created_at + timedelta(minutes=index)
                message_rows.append(
                    Message(
                        id=message_id,
                        conversation_id=conversation_id,
                        role=RoleEnum(role),
                        content=content,
                        created_at=created_at,
                        updated_at=created_at,
                    ).model_dump()
                )
    if conversation_rows:
        await session.execute(
            insert(Conversation)
            .values(conversation_rows)
            .on_conflict_do_nothing(index_elements=["id"])
        )
    if message_rows:
        await session.execute(
            insert(Message)
            .values(message_rows)
            .on_conflict_do_nothing(index_elements=["id"])
        )
    await session.commit()


async def simulate_upload(job_id: str, conversation_id: UUID) -> None:
    updates = [
        JobProgress(stage="upload", message="Document Uploaded", progress=10),
        JobProgress(
            stage="extracting", message="Extracting text from document", progress=30
        ),
        JobProgress(
            stage="chunking", message="Document prepared for embedding", progress=50
        ),
        JobProgress(stage="embedding", message="Generating embeddings", progress=70),
        JobProgress(stage="storing", message="Storing vectors", progress=90),
        JobProgress(
            stage="completed",
            message="Document processing completed",
            progress=100,
            conversation_id=conversation_id,
        ),
    ]

    queue = job_queues[job_id]
    for index, update in enumerate(updates):
        if index:
            await asyncio.sleep(config.MOCK_STATUS_DELAY_SECONDS)
        await queue.put(update)

    asyncio.get_running_loop().call_later(300, job_queues.pop, job_id, None)


@router.post("/embeddings/upload-file", response_model=UploadResponse)
async def upload_file(
    file: Annotated[UploadFile, File(description="PDF or DOCX documents")],
    session: SessionDep,
) -> UploadResponse:
    filename = file.filename

    if not filename:
        raise HTTPException(status_code=400, detail="A file is required")

    extension = "." + filename.rsplit(".", 1)[-1].lower()
    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=400, detail="Only PDF and DOCX documents are supported"
        )

    job_id = str(uuid4())
    file_type: FileType = "pdf" if extension == ".pdf" else "docx"
    conversation_id = uuid4()
    document_counts[conversation_id] = 2 + len(uploads) % 7
    uploads[job_id] = (conversation_id, filename, file_type)
    conversation = Conversation(
        id=conversation_id, user_id="mock-user", title=Path(filename).stem
    )
    session.add(conversation)
    await session.commit()
    conversations[conversation_id] = conversation
    conversation_files[conversation_id] = (filename, file_type)
    job_queues[job_id] = asyncio.Queue()
    await asyncio.sleep(config.MOCK_UPLOAD_DELAY_SECONDS)
    asyncio.create_task(simulate_upload(job_id, conversation_id))
    return UploadResponse(job_id=job_id, filename=filename)


async def get_job_queue(job_id: str) -> asyncio.Queue[JobProgress]:
    queue = job_queues.get(job_id)
    if queue is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return queue


@router.get("/embeddings/upload-status/{job_id}", response_class=EventSourceResponse)
async def upload_status(
    job_id: str,
    queue: Annotated[asyncio.Queue[JobProgress], Depends(get_job_queue)],
):
    while True:
        update = await queue.get()
        yield ServerSentEvent(data={"job_id": job_id, **update.model_dump(mode="json")})
        if update.stage == "completed":
            job_queues.pop(job_id, None)
            break


@router.post("/chat/conversations/{conversation_id}/query", response_model=ChatResponse)
async def query_chatbot(
    conversation_id: UUID, chat_request: ChatRequest, session: SessionDep,
    current_user: CurrentUserDep,
) -> ChatResponse | StreamingResponse:
    await seed_mock_data(session)
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != "mock-user":
        raise HTTPException(status_code=404, detail="Conversation not found")

    await asyncio.sleep(config.MOCK_CHAT_DELAY_SECONDS)
    model = ModelFactory().get_chat_model(
        provider=chat_request.model_provider,
        model_options=chat_request.model_options,
    )
    chain = model | StrOutputParser()
    prompt = [HumanMessage(content=chat_request.message)]
    source_documents = mock_source_documents(conversation_id)
    query_day = await reserve_query(session, current_user)

    if chat_request.is_stream:

        async def generate() -> AsyncGenerator[str]:
            answer_parts: list[str] = []
            completed = False
            try:
                await create_message(session, conversation_id, RoleEnum.USER, chat_request.message)
                async for token in chain.astream(prompt):
                    if token:
                        answer_parts.append(token)
                        yield f"{ChatStreamChunk(token=token).model_dump_json()}\n"
                await create_message(
                    session, conversation_id, RoleEnum.ASSISTANT, "".join(answer_parts)
                )
                await session.commit()
                completed = True
                completion = MockChatStreamComplete(
                    token="",
                    conversation_id=conversation_id,
                    response="".join(answer_parts),
                    source_documents=source_documents,
                )
                yield f"{completion.model_dump_json()}\n"
            except BaseException:
                await session.rollback()
                if not completed:
                    await refund_query(session, current_user, query_day)
                raise

        return StreamingResponse(generate(), media_type="application/x-ndjson")

    try:
        answer = await chain.ainvoke(prompt)
        await create_message(session, conversation_id, RoleEnum.USER, chat_request.message)
        await create_message(session, conversation_id, RoleEnum.ASSISTANT, answer)
        await session.commit()
    except BaseException:
        await session.rollback()
        await refund_query(session, current_user, query_day)
        raise

    return ChatResponse(
        conversation_id=conversation_id,
        response=answer,
        source_documents=source_documents,
    )


@router.get("/chat/conversations", response_model=list[Conversation])
async def get_user_conversations(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[Conversation]:
    await seed_mock_data(session)
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == "mock-user")
        .order_by(col(Conversation.updated_at).desc())
        .limit(limit)
    )
    return list(result.scalars().all())


@router.get("/chat/conversations/{conversation_id}", response_model=ConversationHeader)
async def get_conversation(conversation_id: UUID, session: SessionDep) -> ConversationHeader:
    await seed_mock_data(session)
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != "mock-user":
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationHeader(
        id=conversation.id,
        title=conversation.title,
        document_count=document_counts.get(conversation_id, 2),
    )


@router.get(
    "/chat/conversations/{conversation_id}/messages", response_model=list[MockMessageResponse]
)
async def get_user_messages_for_conversation(
    conversation_id: UUID, session: SessionDep
) -> list[MockMessageResponse]:
    await seed_mock_data(session)
    conversation = await session.get(Conversation, conversation_id)
    if conversation is None or conversation.user_id != "mock-user":
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await get_messages_for_conversation(session, conversation_id)
    sources = mock_source_documents(conversation_id)
    return [
        MockMessageResponse.model_validate(
            {
                **message.model_dump(),
                "source_documents": sources if message.role == RoleEnum.ASSISTANT else [],
            }
        )
        for message in messages
    ]
