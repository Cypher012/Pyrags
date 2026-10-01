import asyncio
import logging
from io import BytesIO
from typing import Literal

from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.chat.service import clear_rag_chain_cache
from app.embeddings.documents import DocumentChunk, DocumentMetadata
from app.embeddings.schemas import JobProgress
from app.embeddings.service import generate_embeddings, store_vectors

logger = logging.getLogger(__name__)

FileType = Literal["pdf", "docx"]
SourcePart = tuple[int | None, str]


def extract_pdf_pages(content: bytes) -> list[SourcePart]:
    """Extract PDF text while preserving one-based page numbers."""

    reader = PdfReader(BytesIO(content))

    return [
        (page_number, page.extract_text() or "")
        for page_number, page in enumerate(reader.pages, start=1)
    ]


def extract_text_from_word_bytes(content: bytes) -> str:
    """Extract text from a Word document."""

    doc = Document(BytesIO(content))

    return "\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text)


def extract_document(
    content: bytes,
    filename: str,
) -> tuple[FileType, list[SourcePart]]:
    """Extract text from an uploaded document."""

    extension = filename.lower().rsplit(".", 1)[-1]

    if extension == "pdf":
        return "pdf", extract_pdf_pages(content)

    if extension == "docx":
        return "docx", [(None, extract_text_from_word_bytes(content))]

    raise ValueError("Unsupported file format")


def split_text_into_chunks(text: str) -> list[str]:
    """Split text into smaller chunks."""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],
    )

    return text_splitter.split_text(text)


def chunk_document(
    source_parts: list[SourcePart],
    filename: str,
    file_type: FileType,
) -> list[DocumentChunk]:
    """Turn extracted document text into metadata-aware chunks."""

    chunks: list[DocumentChunk] = []

    for page_number, page_text in source_parts:
        if not page_text.strip():
            continue

        for chunk_text in split_text_into_chunks(page_text):
            chunks.append(
                DocumentChunk(
                    content=chunk_text,
                    metadata=DocumentMetadata(
                        file_name=filename,
                        file_type=file_type,
                        page_number=page_number,
                        chunk_index=len(chunks),
                    ),
                )
            )

    return chunks


async def run_embeddings_job(
    job_queues: dict[str, asyncio.Queue[JobProgress]],
    job_id: str,
    content: bytes,
    filename: str,
):
    queue = job_queues[job_id]

    try:
        await queue.put(
            JobProgress(stage="upload", message="Document Uploaded", progress=10)
        )

        await queue.put(
            JobProgress(
                stage="extracting", message="Extracting text from document", progress=30
            )
        )

        file_type, source_parts = await asyncio.to_thread(
            extract_document, content, filename
        )

        if not any(text.strip() for _, text in source_parts):
            raise ValueError("No text could be extracted from the file")

        await queue.put(
            JobProgress(
                stage="chunking", message="Document prepared for embedding", progress=50
            )
        )

        doc_chunks = await asyncio.to_thread(
            chunk_document,
            source_parts,
            filename,
            file_type,
        )

        if not doc_chunks:
            raise ValueError("No document chunks could be created")

        await queue.put(
            JobProgress(
                stage="embedding",
                message="Generating embeddings",
                progress=70,
            )
        )

        embedded_chunks = await asyncio.to_thread(
            generate_embeddings,
            doc_chunks,
        )

        await queue.put(
            JobProgress(
                stage="storing",
                message="Storing vectors",
                progress=90,
            )
        )

        result = await asyncio.to_thread(
            store_vectors,
            embedded_chunks,
        )

        if result.status == "error":
            raise RuntimeError(result.message)

        await queue.put(
            JobProgress(stage="storing", message="Embeddings stored", progress=90)
        )

        clear_rag_chain_cache()

        await queue.put(
            JobProgress(
                stage="completed", message="Document processing completed", progress=100
            )
        )

    except Exception as exc:
        logger.exception("Error processing job %s", job_id)

        await queue.put(JobProgress(stage="error", message=str(exc), progress=0))
