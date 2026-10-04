import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Literal
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.core.database import async_session
from app.embeddings.documents import DocumentMetadata, PreparedChunk
from app.embeddings.schemas import JobProgress
from app.embeddings.service import generate_embeddings
from app.model.conversation import ConversationCreate
from app.model.document import DocumentCreate, DocumentStatus
from app.model.document_chunk import DocumentChunk
from app.repository.conversation import create_conversation
from app.repository.document import create_document, update_document_status
from app.repository.document_chunk import create_document_chunks

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


def extract_docx_page_count(content: bytes) -> int | None:
    try:
        with ZipFile(BytesIO(content)) as archive:
            if archive.getinfo("docProps/app.xml").file_size > 64 * 1024:
                return None
            properties = ElementTree.fromstring(archive.read("docProps/app.xml"))
        value = properties.findtext(
            "{http://schemas.openxmlformats.org/officeDocument/2006/extended-properties}Pages"
        )
        if value is None:
            return None
        page_count = int(value)
        return page_count if page_count > 0 else None
    except (BadZipFile, KeyError, ValueError, ElementTree.ParseError):
        return None


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
) -> list[PreparedChunk]:
    """Turn extracted document text into metadata-aware chunks."""

    chunks: list[PreparedChunk] = []

    for page_number, page_text in source_parts:
        if not page_text.strip():
            continue

        for chunk_text in split_text_into_chunks(page_text):
            chunks.append(
                PreparedChunk(
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
    user_id: str,
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
        page_count = (
            len(source_parts)
            if file_type == "pdf"
            else await asyncio.to_thread(extract_docx_page_count, content)
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

        async with async_session() as session, session.begin():
            conversation = await create_conversation(
                session=session,
                data=ConversationCreate(user_id=user_id, title=Path(filename).stem),
            )

            document = await create_document(
                session=session,
                data=DocumentCreate(
                    conversation_id=conversation.id,
                    file_name=filename,
                    file_type=file_type,
                    status=DocumentStatus.PROCESSING,
                    size_bytes=len(content),
                    page_count=page_count,
                ),
            )

            database_chunks = [
                DocumentChunk(
                    document_id=document.id,
                    content=chunk.content,
                    page_number=chunk.metadata.page_number,
                    chunk_index=chunk.metadata.chunk_index,
                    embedding=chunk.embedding,
                )
                for chunk in embedded_chunks
            ]

            await create_document_chunks(session=session, chunks=database_chunks)

            await update_document_status(
                session=session, document=document, status=DocumentStatus.READY
            )

        await queue.put(
            JobProgress(
                stage="completed",
                message="Document processing completed",
                progress=100,
                conversation_id=conversation.id,
            )
        )

    except Exception as exc:
        logger.exception("Error processing job %s", job_id)

        await queue.put(JobProgress(stage="error", message=str(exc), progress=0))
