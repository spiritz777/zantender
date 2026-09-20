import asyncio
from pathlib import Path

import fitz
import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings
from app.database.models import Document, DocumentChunk
from app.documents.exceptions import DocumentTooLargeError
from app.services.document_service import DocumentService
from app.services.user_service import UserService


def _pdf_bytes(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    data = document.tobytes()
    document.close()
    return data


def test_ingest_pdf_persists_chunks(
    tmp_path: Path, settings: Settings, session_factory: sessionmaker[Session]
) -> None:
    user = asyncio.run(
        UserService(session_factory).ensure_telegram_user(1, "alice", "Alice")
    )
    service = DocumentService(session_factory, settings, uploads_dir=tmp_path)

    processed = asyncio.run(
        service.ingest_bytes(
            user_id=user.id,
            filename="tender.pdf",
            data=_pdf_bytes("Deliver equipment by 15 May"),
        )
    )

    assert processed.filename == "tender.pdf"
    assert processed.page_count == 1
    assert "equipment" in processed.chunks[0].text
    with session_factory() as session:
        stored = session.get(Document, processed.document_id)
        assert stored is not None
        assert session.query(DocumentChunk).count() == 1

    context = asyncio.run(service.get_latest_context(user.id, max_chars=200))
    assert context is not None
    assert context[0] == "tender.pdf"
    assert "15 May" in context[1]


def test_ingest_rejects_oversized_file(
    tmp_path: Path, settings: Settings, session_factory: sessionmaker[Session]
) -> None:
    user = asyncio.run(
        UserService(session_factory).ensure_telegram_user(2, None, None)
    )
    service = DocumentService(session_factory, settings, uploads_dir=tmp_path)

    with pytest.raises(DocumentTooLargeError):
        asyncio.run(
            service.ingest_bytes(
                user_id=user.id,
                filename="huge.pdf",
                data=b"a" * (settings.max_file_size_bytes + 1),
            )
        )
