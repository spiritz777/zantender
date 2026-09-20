"""Create and run the aiogram application."""

from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage

from app.ai.providers.base import AIProvider
from app.ai.service import create_ai_provider
from app.bot.handlers import router
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


logger = logging.getLogger(__name__)


def create_dispatcher(
    user_service: UserService,
    ai_provider: AIProvider,
    document_service: DocumentService,
    analysis_service: AnalysisService,
    consultant_service: ConsultantService,
    company_profile_service: CompanyProfileService,
    tender_catalog_service: TenderCatalogService,
    notification_service: NotificationService,
    settings: Settings,
) -> Dispatcher:
    """Configure aiogram routers and dependency injection for this MVP."""
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher["user_service"] = user_service
    dispatcher["ai_provider"] = ai_provider
    dispatcher["document_service"] = document_service
    dispatcher["analysis_service"] = analysis_service
    dispatcher["consultant_service"] = consultant_service
    dispatcher["company_profile_service"] = company_profile_service
    dispatcher["tender_catalog_service"] = tender_catalog_service
    dispatcher["notification_service"] = notification_service
    dispatcher["settings"] = settings
    dispatcher.include_router(router)
    return dispatcher


async def run_polling(settings: Settings, user_service: UserService) -> None:
    """Start long polling and close the HTTP session during shutdown."""
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required to start Telegram polling.")

    ai_provider = create_ai_provider(settings)
    document_service = DocumentService(user_service.session_factory, settings)
    analysis_service = AnalysisService(
        user_service.session_factory, ai_provider, settings
    )
    consultant_service = ConsultantService(ai_provider, document_service, settings)
    company_profile_service = CompanyProfileService(user_service.session_factory)
    tender_catalog_service = TenderCatalogService(
        user_service.session_factory,
        DemoTenderSource(),
        company_profile_service,
        MatchingService(),
    )
    notification_service = NotificationService(user_service.session_factory)
    bot = Bot(token=settings.bot_token)
    dispatcher = create_dispatcher(
        user_service,
        ai_provider,
        document_service,
        analysis_service,
        consultant_service,
        company_profile_service,
        tender_catalog_service,
        notification_service,
        settings,
    )
    try:
        # A bot can receive updates through only one delivery method at a time.
        # This safely switches a previously configured webhook to long polling.
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Telegram polling started")
        await dispatcher.start_polling(
            bot, allowed_updates=dispatcher.resolve_used_update_types()
        )
    except TelegramNetworkError as error:
        logger.error(
            "Cannot connect to Telegram. Check Internet access, VPN/proxy and firewall."
        )
        raise RuntimeError("Telegram connection is unavailable.") from error
    finally:
        await bot.session.close()
