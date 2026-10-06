from io import BytesIO
from typing import Literal
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile

from docx import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.embeddings.documents import DocumentMetadata, PreparedChunk

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
