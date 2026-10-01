from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, ConfigDict, Field

from app.chat.model import ChatModelConfig, ModelProvider
from app.embeddings.documents import SourceDocument


class ChatRequest(BaseModel):
    """HTTP request for a conversational RAG query."""

    session_id: str | None = Field(default=None, min_length=1)
    message: str = Field(min_length=1)
    is_stream: bool = False
    model_provider: ModelProvider = ModelProvider.OPENAI
    model_options: ChatModelConfig = Field(default_factory=ChatModelConfig)


class ChatResponse(BaseModel):
    """HTTP response for a non-streaming chat query."""

    session_id: str
    response: str
    source_documents: list[SourceDocument] = Field(default_factory=list)


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
    """One JSON-serializable event emitted by the streaming endpoint."""

    token: str


class RagChainRequest(BaseModel):
    """Typed request adapted to the mapping-based LangChain runnable."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    input: str = Field(min_length=1)
    chat_history: list[BaseMessage] = Field(default_factory=list)

    def as_langchain_input(self) -> dict[str, object]:
        """Convert the validated request to the shape expected by LCEL."""

        return {
            "input": self.input,
            "chat_history": self.chat_history,
        }


class RagChainResponse(BaseModel):
    """Validated non-streaming result produced by the retrieval chain."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    answer: str
    context: list[Document] = Field(default_factory=list)


class RagChainChunk(BaseModel):
    """Validated partial result produced while the retrieval chain streams."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")

    answer: str | None = None
    context: list[Document] = Field(default_factory=list)
