"""Page-aware, word-safe text chunking."""

from __future__ import annotations

from app.documents.schemas import DocumentChunkData, DocumentPage


def clean_text(text: str) -> str:
    return " ".join(text.split())


def chunk_pages(pages: list[DocumentPage], max_chars: int) -> list[DocumentChunkData]:
    """Create chunks close to ``max_chars`` without splitting ordinary words."""
    chunks: list[DocumentChunkData] = []
    buffer: list[str] = []
    page_start: int | None = None
    page_end: int | None = None
    buffer_length = 0

    def flush() -> None:
        nonlocal buffer, page_start, page_end, buffer_length
        if not buffer or page_start is None or page_end is None:
            return
        chunks.append(
            DocumentChunkData(
                chunk_index=len(chunks),
                page_start=page_start,
                page_end=page_end,
                text=" ".join(buffer),
            )
        )
        buffer = []
        page_start = None
        page_end = None
        buffer_length = 0

    for page in pages:
        text = clean_text(page.text)
        if not text:
            continue
        for word in text.split():
            separator_length = 1 if buffer else 0
            if buffer and buffer_length + separator_length + len(word) > max_chars:
                flush()
            if page_start is None:
                page_start = page.page_number
            page_end = page.page_number
            buffer.append(word)
            buffer_length += separator_length + len(word)
    flush()
    return chunks
