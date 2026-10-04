from langchain_openai import OpenAIEmbeddings
from pydantic import BaseModel, SecretStr

from app.core.config import config
from app.embeddings.documents import DocumentMetadata, PreparedChunk


class EmbeddedChunk(BaseModel):
    content: str
    embedding: list[float]
    metadata: DocumentMetadata


def get_embedding_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model="text-embedding-3-large",
        dimensions=1024,
        api_key=SecretStr(config.OPENAI_API_KEY),
    )


def generate_query_embedding(query: str) -> list[float]:
    embeddings = get_embedding_model()
    return embeddings.embed_query(query)


def generate_embeddings(
    doc_chunks: list[PreparedChunk],
) -> list[EmbeddedChunk]:
    embeddings = get_embedding_model()

    texts = [chunk.content for chunk in doc_chunks]

    vectors = embeddings.embed_documents(texts)

    return [
        EmbeddedChunk(
            content=chunk.content,
            embedding=vector,
            metadata=chunk.metadata,
        )
        for chunk, vector in zip(doc_chunks, vectors, strict=True)
    ]
