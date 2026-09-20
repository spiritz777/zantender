import asyncio
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from app.ai.providers.demo import DemoAIProvider
from app.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.company_profile_service import CompanyProfileService
from app.services.consultant_service import ConsultantService
from app.services.document_service import DocumentService
from app.services.matching_service import MatchingService
from app.services.notification_service import NotificationService
from app.services.tender_catalog_service import TenderCatalogService
from app.services.user_service import UserService
from app.tenders.demo_source import DemoTenderSource


def test_full_demo_scenario_runs_offline(
    tmp_path: Path, settings: Settings, session_factory: sessionmaker[Session]
) -> None:
    user = asyncio.run(
        UserService(session_factory).ensure_telegram_user(99, "demo", "Demo")
    )
    profiles = CompanyProfileService(session_factory)
    asyncio.run(
        profiles.save_description(user.id, "Компания занимается разработкой сайтов")
    )
    catalogue = TenderCatalogService(
        session_factory, DemoTenderSource(), profiles, MatchingService()
    )

    matches = asyncio.run(catalogue.find_matches(user.id))

    assert matches[0].tender.title == "Разработка корпоративного сайта"
    assert matches[0].tender.amount == 2450000
    assert matches[0].score == 91

    selected = asyncio.run(catalogue.save_selected(user.id, matches[0].tender))
    documents = DocumentService(session_factory, settings, uploads_dir=tmp_path)
    processed = asyncio.run(
        documents.ingest_text(
            user_id=user.id,
            filename="demo.txt",
            text=matches[0].tender.document_text,
            tender_id=selected.id,
        )
    )
    provider = DemoAIProvider()
    analysis = asyncio.run(
        AnalysisService(session_factory, provider, settings).analyze(processed)
    )

    assert analysis.score == 82
    answer = asyncio.run(
        ConsultantService(provider, documents, settings).answer(
            user_id=user.id, question="Почему этот тендер мне подходит?"
        )
    )
    assert "разработка корпоративного сайта" in answer

    notifications = NotificationService(session_factory)
    assert asyncio.run(notifications.is_enabled(user.id)) is True
    assert asyncio.run(notifications.set_enabled(user.id, False)) is False
    assert asyncio.run(notifications.is_enabled(user.id)) is False


def test_demo_mode_selects_offline_ai_provider(settings: Settings) -> None:
    from app.ai.service import create_ai_provider

    assert isinstance(create_ai_provider(settings), DemoAIProvider)
