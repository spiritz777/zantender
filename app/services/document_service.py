"""Store uploaded tender documents and retrieve text context."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.config import Settings
from app.database.database import session_scope
from app.database.models import Document, DocumentChunk, Tender, User
from app.documents.chunking import chunk_pages
from app.documents.processor import detect_file_type, ensure_file_size, extract_pages
from app.documents.schemas import DocumentChunkData, DocumentPage, ProcessedDocument


class DocumentService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        settings: Settings,
        *,
        uploads_dir: Path | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._uploads_dir = uploads_dir or settings.uploads_dir

    async def ingest_bytes(
        self,
        *,
        user_id: int,
        filename: str,
        data: bytes,
        mime_type: str | None = None,
        tender_id: int | None = None,
    ) -> ProcessedDocument:
        ensure_file_size(len(data), self._settings)
        file_type = detect_file_type(filename, mime_type)
        stored_path = await asyncio.to_thread(self._store_file, user_id, filename, data)
        try:
            pages = await extract_pages(stored_path, file_type)
            chunks = chunk_pages(pages, self._settings.chunk_size_chars)
            return await asyncio.to_thread(
                self._persist,
                user_id,
                filename,
                stored_path,
                file_type,
                pages,
                chunks,
                tender_id,
            )
        except Exception:
            stored_path.unlink(missing_ok=True)
            raise

    async def ingest_text(
        self,
        *,
        user_id: int,
        text: str,
        filename: str = "specification.txt",
        tender_id: int | None = None,
    ) -> ProcessedDocument:
        return await self.ingest_bytes(
            user_id=user_id,
            filename=filename,
            data=text.encode("utf-8"),
            mime_type="text/plain",
            tender_id=tender_id,
        )

    async def get_latest_context(
        self, user_id: int, max_chars: int
    ) -> tuple[str, str] | None:
        return await asyncio.to_thread(self._get_latest_context, user_id, max_chars)

    def _store_file(self, user_id: int, filename: str, data: bytes) -> Path:
        directory = self._uploads_dir / str(user_id)
        directory.mkdir(parents=True, exist_ok=True)
        suffix = Path(filename).suffix.lower() or ".bin"
        stored_path = directory / f"{uuid4().hex}{suffix}"
        stored_path.write_bytes(data)
        return stored_path

    def _persist(
        self,
        user_id: int,
        filename: str,
        stored_path: Path,
        file_type: str,
        pages: list[DocumentPage],
        chunks: list[DocumentChunkData],
        tender_id: int | None,
    ) -> ProcessedDocument:
        with session_scope(self._session_factory) as session:
            user = session.get(User, user_id)
            if user is None:
                raise ValueError("User does not exist.")
            if tender_id is not None:
                tender = session.get(Tender, tender_id)
                if tender is None or tender.user_id != user_id:
                    raise ValueError("Tender does not belong to this user.")
            document = Document(
                user_id=user_id,
                tender_id=tender_id,
                filename=filename,
                file_path=str(stored_path),
                file_type=file_type,
                page_count=len(pages),
            )
            session.add(document)
            session.flush()
            for chunk in chunks:
                session.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=chunk.chunk_index,
                        page_start=chunk.page_start,
                        page_end=chunk.page_end,
                        text=chunk.text,
                    )
                )
            return ProcessedDocument(
                document_id=document.id,
                filename=filename,
                file_path=stored_path,
                file_type=file_type,
                page_count=len(pages),
                chunks=chunks,
            )

    def _get_latest_context(self, user_id: int, max_chars: int) -> tuple[str, str] | None:
        with session_scope(self._session_factory) as session:
            document = session.scalar(
                select(Document)
                .options(selectinload(Document.chunks))
                .where(Document.user_id == user_id)
                .order_by(Document.created_at.desc(), Document.id.desc())
            )
            if document is None or not document.chunks:
                return None
            parts: list[str] = []
            used = 0
            for chunk in document.chunks:
                remaining = max_chars - used
                if remaining <= 0:
                    break
                text = chunk.text[:remaining]
                parts.append(text)
                used += len(text)
            context = "\n\n".join(parts).strip()
            if not context:
                return None
            return document.filename, context
