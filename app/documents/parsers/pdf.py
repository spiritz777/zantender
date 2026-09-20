"""PDF text extraction via PyMuPDF."""

from __future__ import annotations

import asyncio
from pathlib import Path

import fitz

from app.documents.exceptions import DocumentProcessingError
from app.documents.parsers.base import DocumentParser
from app.documents.schemas import DocumentPage


class PDFParser(DocumentParser):
    async def parse(self, file_path: Path) -> list[DocumentPage]:
        return await asyncio.to_thread(self._parse, file_path)

    def _parse(self, file_path: Path) -> list[DocumentPage]:
        try:
            with fitz.open(file_path) as document:
                return [
                    DocumentPage(page_number=index, text=page.get_text() or "")
                    for index, page in enumerate(document, start=1)
                ]
        except DocumentProcessingError:
            raise
        except Exception as error:
            raise DocumentProcessingError("Не удалось прочитать PDF-файл.") from error
