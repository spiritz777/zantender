"""Plain-text specification parser."""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.documents.exceptions import DocumentProcessingError
from app.documents.parsers.base import DocumentParser
from app.documents.schemas import DocumentPage


class TXTParser(DocumentParser):
    async def parse(self, file_path: Path) -> list[DocumentPage]:
        return await asyncio.to_thread(self._parse, file_path)

    def _parse(self, file_path: Path) -> list[DocumentPage]:
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = file_path.read_text(encoding="cp1251")
            except Exception as error:
                raise DocumentProcessingError(
                    "Не удалось прочитать текстовый файл."
                ) from error
        except Exception as error:
            raise DocumentProcessingError("Не удалось прочитать текстовый файл.") from error
        return [DocumentPage(page_number=1, text=text)]
