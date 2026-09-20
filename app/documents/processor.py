"""Validate an upload and extract page text for later chunking."""

from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.documents.chunking import clean_text
from app.documents.exceptions import (
    DocumentTooLargeError,
    EmptyDocumentError,
    UnsupportedDocumentError,
)
from app.documents.parsers.docx import DOCXParser
from app.documents.parsers.pdf import PDFParser
from app.documents.parsers.txt import TXTParser
from app.documents.schemas import DocumentPage

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "docx",
    ".txt": "txt",
}

_PARSERS = {
    "pdf": PDFParser(),
    "docx": DOCXParser(),
    "txt": TXTParser(),
}


def detect_file_type(filename: str, mime_type: str | None = None) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in SUPPORTED_EXTENSIONS:
        return SUPPORTED_EXTENSIONS[suffix]
    if mime_type == "application/pdf":
        return "pdf"
    if mime_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return "docx"
    if mime_type in {"text/plain", "text/txt"}:
        return "txt"
    raise UnsupportedDocumentError("Поддерживаются только PDF, DOCX и текстовые файлы.")


def ensure_file_size(size_bytes: int, settings: Settings) -> None:
    if size_bytes > settings.max_file_size_bytes:
        raise DocumentTooLargeError(
            f"Файл больше допустимого размера {settings.max_file_size_mb} МБ."
        )


async def extract_pages(file_path: Path, file_type: str) -> list[DocumentPage]:
    parser = _PARSERS.get(file_type)
    if parser is None:
        raise UnsupportedDocumentError("Поддерживаются только PDF, DOCX и текстовые файлы.")
    pages = await parser.parse(file_path)
    if not any(clean_text(page.text) for page in pages):
        raise EmptyDocumentError(
            "В файле нет извлекаемого текста. Сканы без текстового слоя пока не поддерживаются."
        )
    return pages
