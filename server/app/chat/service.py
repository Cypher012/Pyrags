from collections.abc import AsyncGenerator
from typing import cast

from langchain_classic.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable

from app.chat.model import ChatModelConfig, ModelProvider
from app.chat.model_factory import ModelFactory
from app.chat.prompts import SYSTEM_PROMPT
from app.chat.schemas import (
    ChatServiceRequest,
    ChatServiceResponse,
    ChatStreamChunk,
    RagChainChunk,
    RagChainRequest,
    RagChainResponse,
)
from app.embeddings.documents import SourceDocument
from app.embeddings.service import create_pinecone_index

# LangChain's LCEL retrieval chain uses mappings internally. The application
# boundary is kept typed with RagChainRequest/RagChainResponse below.
RagChain = Runnable[dict[str, object], dict[str, object]]

_rag_chain_cache: dict[str, RagChain] = {}


def _make_cache_key(
    model_provider: ModelProvider,
    model_options: ChatModelConfig | None,
) -> str:
    """Build a stable cache key from the provider and validated options."""

    options = model_options or ChatModelConfig()
    return f"{model_provider}:{options.model_dump_json()}"


def create_chat_prompt() -> ChatPromptTemplate:
    """Prompt used to generate the final answer."""

    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Context:\n{context}\n\nQuestion:\n{input}"),
        ]
    )


def create_history_aware_prompt() -> ChatPromptTemplate:
    """Prompt used to turn a follow-up question into a standalone question."""

    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "Question: {input}"),
        ]
    )


def _build_rag_chain(
    model_provider: ModelProvider,
    model_options: ChatModelConfig,
) -> RagChain:
    """Build the mapping-based LangChain RAG pipeline."""

    vector_store = create_pinecone_index()
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )

    model = ModelFactory().get_chat_model(
        provider=model_provider,
        model_options=model_options,
    )

    history_aware_retriever = create_history_aware_retriever(
        model,
        retriever,
        create_history_aware_prompt(),
    )

    qa_chain = create_chat_prompt() | model | StrOutputParser()
    chain = create_retrieval_chain(history_aware_retriever, qa_chain)

    # The third-party chain exposes the same mapping shape at runtime; the
    # cast isolates that implementation detail from the typed app boundary.
    return cast(RagChain, chain)


def create_rag_chain(
    model_provider: ModelProvider = ModelProvider.OPENAI,
    model_options: ChatModelConfig | None = None,
) -> RagChain:
    """Get or build the cached RAG pipeline for validated model options."""

    options = model_options or ChatModelConfig()
    cache_key = _make_cache_key(model_provider, options)

    if cache_key not in _rag_chain_cache:
        _rag_chain_cache[cache_key] = _build_rag_chain(model_provider, options)

    return _rag_chain_cache[cache_key]


def clear_rag_chain_cache() -> None:
    """Drop all cached chains, forcing a rebuild on the next request."""

    _rag_chain_cache.clear()


async def query_bot(request: ChatServiceRequest) -> ChatServiceResponse:
    """Run a validated non-streaming RAG query."""

    rag_chain = create_rag_chain(
        model_provider=request.model_provider,
        model_options=request.model_options,
    )
    rag_request = RagChainRequest(
        input=request.message,
        chat_history=request.chat_history,
    )

    raw_response = await rag_chain.ainvoke(rag_request.as_langchain_input())
    response = RagChainResponse.model_validate(raw_response)

    return ChatServiceResponse(
        answer=response.answer,
        source_documents=[
            SourceDocument.from_langchain_document(document)
            for document in response.context
        ],
    )


async def stream_bot(
    request: ChatServiceRequest,
) -> AsyncGenerator[ChatStreamChunk]:
    """Stream validated answer chunks from the RAG pipeline."""

    rag_chain = create_rag_chain(
        model_provider=request.model_provider,
        model_options=request.model_options,
    )
    rag_request = RagChainRequest(
        input=request.message,
        chat_history=request.chat_history,
    )

    async for raw_chunk in rag_chain.astream(rag_request.as_langchain_input()):
        chunk = RagChainChunk.model_validate(raw_chunk)
        if chunk.answer:
            yield ChatStreamChunk(token=chunk.answer)
