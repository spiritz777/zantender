import asyncio
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.ai.providers.mock import MockAIProvider
from app.ai.schemas import TenderAnalysisResult
from app.config import Settings
from app.services.analysis_service import AnalysisService, format_analysis, format_history
from app.services.document_service import DocumentService
from app.services.user_service import UserService


def test_analyze_saves_structured_result(
    tmp_path: Path, settings: Settings, session_factory: sessionmaker[Session]
) -> None:
    user = asyncio.run(
        UserService(session_factory).ensure_telegram_user(10, None, "Bob")
    )
    documents = DocumentService(session_factory, settings, uploads_dir=tmp_path)
    processed = asyncio.run(
        documents.ingest_text(
            user_id=user.id,
            text="Поставка бумаги. Срок: 10 дней. Нужна лицензия.",
        )
    )
    provider = MockAIProvider(
        structured_response=TenderAnalysisResult(
            title="Поставка бумаги",
            customer="ГП",
            summary="Нужно поставить бумагу за 10 дней.",
            requirements=["поставить бумагу"],
            required_documents=["лицензия"],
            deadlines=["10 дней"],
            risks=["короткий срок"],
            score=74,
            recommendation="Уточнить объём и условия поставки.",
        )
    )
    service = AnalysisService(session_factory, provider, settings)

    analysis = asyncio.run(service.analyze(processed))
    rendered = format_analysis(processed, analysis)

    assert analysis.score == 74
    assert "лицензия" in rendered
    assert "74/100" in rendered
    history = asyncio.run(service.list_recent(user.id))
    assert format_history(history).count("Поставка") >= 0
    assert "74/100" in format_history(history)
