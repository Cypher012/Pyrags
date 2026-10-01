import time
from uuid import uuid4

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient
from pinecone import ServerlessSpec, Vector
from pydantic import BaseModel, SecretStr

from app.embeddings.documents import DocumentChunk
from app.embeddings.schemas import EmbeddingResponse
from config import config

pc = PineconeClient(api_key=config.PINECONE_API_KEY)


class EmbeddedChunk(BaseModel):
    content: str
    embedding: list[float]
    metadata: dict


def get_embeddings_function() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-large",
        dimensions=1024,
        api_key=SecretStr(config.OPENAI_API_KEY),
    )


def get_pinecone_index():
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    if config.PINECONE_INDEX_NAME not in existing_indexes:
        _ = pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=1024,
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",
            ),
        )

        while not pc.describe_index(config.PINECONE_INDEX_NAME).status["ready"]:
            time.sleep(1)

    return pc.Index(config.PINECONE_INDEX_NAME)


def delete_pinecone_index() -> bool:
    try:
        existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]
        if config.PINECONE_INDEX_NAME in existing_indexes:
            _ = pc.delete_index(config.PINECONE_INDEX_NAME)
            time.sleep(2)
        return True
    except Exception as exc:  # noqa: BLE001 - return a safe result at the infrastructure boundary
        print(f"Error deleting index: {exc}")
        return False


def create_pinecone_index() -> PineconeVectorStore:
    existing_indexes = [index_info["name"] for index_info in pc.list_indexes()]

    if config.PINECONE_INDEX_NAME not in existing_indexes:
        _ = pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=1024,
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

        while not pc.describe_index(config.PINECONE_INDEX_NAME).status["ready"]:
            time.sleep(1)

    return PineconeVectorStore(
        index=pc.Index(name=config.PINECONE_INDEX_NAME),
        embedding=get_embeddings_function(),
        text_key="text",
    )


def generate_embeddings(
    doc_chunks: list[DocumentChunk],
) -> list[EmbeddedChunk]:
    embeddings = get_embeddings_function()

    texts = [chunk.content for chunk in doc_chunks]

    vectors = embeddings.embed_documents(texts)

    return [
        EmbeddedChunk(
            content=chunk.content,
            embedding=vector,
            metadata=chunk.metadata.as_pinecone_metadata(),
        )
        for chunk, vector in zip(doc_chunks, vectors, strict=True)
    ]


def store_vectors(
    embedded_chunks: list[EmbeddedChunk],
) -> EmbeddingResponse:
    try:
        _ = delete_pinecone_index()

        index = get_pinecone_index()

        vectors = [
            Vector(
                id=str(uuid4()),
                values=chunk.embedding,
                metadata={
                    "text": chunk.content,
                    **chunk.metadata,
                },
            )
            for chunk in embedded_chunks
        ]

        index.upsert(vectors=vectors)

        return EmbeddingResponse(
            status="success",
            message=(f"Successfully stored {len(embedded_chunks)} chunks"),
            chunk_count=len(embedded_chunks),
        )

    except Exception as exc:
        return EmbeddingResponse(
            status="error",
            message=f"Error storing embeddings: {exc}",
            chunk_count=0,
        )
