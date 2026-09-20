"""Parser contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.documents.schemas import DocumentPage


class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, file_path: Path) -> list[DocumentPage]:
        """Extract text while retaining original page order."""
