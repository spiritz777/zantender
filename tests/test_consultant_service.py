import asyncio
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.ai.prompts.consultant import CONSULTANT_SYSTEM_INSTRUCTION
from app.ai.providers.mock import MockAIProvider
from app.config import Settings
from app.services.consultant_service import ConsultantService, build_consultant_prompt
from app.services.document_service import DocumentService
from app.services.user_service import UserService


def test_build_consultant_prompt_includes_document() -> None:
    prompt = build_consultant_prompt("Какой срок?", ("spec.pdf", "Срок 5 дней"))

    assert "Какой срок?" in prompt
    assert "spec.pdf" in prompt
    assert "Срок 5 дней" in prompt


def test_consultant_uses_latest_document_context(
    tmp_path: Path, settings: Settings, session_factory: sessionmaker[Session]
) -> None:
    user = asyncio.run(
        UserService(session_factory).ensure_telegram_user(3, None, None)
    )
    documents = DocumentService(session_factory, settings, uploads_dir=tmp_path)
    asyncio.run(
        documents.ingest_text(user_id=user.id, text="Обеспечение заявки 1%")
    )
    provider = MockAIProvider(text_response="Обеспечение указано в документе.")
    service = ConsultantService(provider, documents, settings)

    answer = asyncio.run(service.answer(user_id=user.id, question="Какое обеспечение?"))

    assert answer == "Обеспечение указано в документе."
    prompt, instruction = provider.requests[0]
    assert "Обеспечение заявки 1%" in prompt
    assert "Какое обеспечение?" in prompt
    assert instruction == CONSULTANT_SYSTEM_INSTRUCTION
