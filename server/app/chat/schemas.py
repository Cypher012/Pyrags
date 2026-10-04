from uuid import UUID

from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field

from app.chat.model import ChatModelConfig, ModelProvider
from app.embeddings.documents import SourceDocument


class ChatRequest(BaseModel):
    """HTTP request for a conversational RAG query."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "message": "What is 2 + 2?",
                    "is_stream": False,
                    "model_provider": "openai",
                    "model_options": {"model": "gpt-5-nano", "temperature": 0},
                }
            ]
        }
    )

    message: str = Field(min_length=1)
    is_stream: bool = False
    model_provider: ModelProvider = ModelProvider.OPENAI
    model_options: ChatModelConfig = Field(default_factory=ChatModelConfig)


class ChatResponse(BaseModel):
    conversation_id: UUID
    response: str
    source_documents: list[SourceDocument]


class ChatServiceRequest(BaseModel):
    """Validated input passed from the HTTP layer to the chat service."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    message: str = Field(min_length=1)
    chat_history: list[BaseMessage] = Field(default_factory=list)
    model_provider: ModelProvider = ModelProvider.OPENAI
    model_options: ChatModelConfig = Field(default_factory=ChatModelConfig)


class ChatServiceResponse(BaseModel):
    """Validated result returned by the chat service."""

    answer: str
    source_documents: list[SourceDocument] = Field(default_factory=list)


class ChatStreamChunk(BaseModel):
    """One JSON-serializable token event emitted by the streaming endpoint."""

    token: str


class ChatStreamComplete(BaseModel):
    """Final NDJSON event emitted once a streaming reply has been persisted."""

    token: str = ""
    conversation_id: UUID
    response: str
    source_documents: list[SourceDocument] = Field(default_factory=list)
