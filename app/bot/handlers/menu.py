"""Telegram UX handlers; services retain all persistence and domain logic."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from io import BytesIO

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.ai.exceptions import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderTimeoutError,
)
from app.bot.keyboards.main_menu import (
    ANALYZE_BUTTON,
    COMPANY_BUTTON,
    CONSULTANT_BUTTON,
    HISTORY_BUTTON,
    HOW_IT_WORKS_BUTTON,
    MATCHES_BUTTON,
    NOTIFICATIONS_BUTTON,
    analysis_complete_keyboard,
    company_saved_keyboard,
    notifications_keyboard,
    tender_keyboard,
)
from app.bot.states.interaction import (
    CompanyProfileState,
    ConsultantState,
    DocumentAnalysisState,
)
from app.bot.texts import (
    ANALYSIS_MESSAGE,
    ANALYSIS_STARTED_MESSAGE,
    COMPANY_PROMPT,
    COMPANY_SAVED_MESSAGE,
    CONSULTANT_MESSAGE,
    CONSULTANT_PROMPT,
    DOCUMENT_READ_ERROR_MESSAGE,
    EMPTY_DOCUMENT_MESSAGE,
    HOW_IT_WORKS_MESSAGE,
    NO_SPEC_TEXT_MESSAGE,
    NOTIFICATIONS_MESSAGE,
    PROFILE_REQUIRED_MESSAGE,
    TEST_NOTIFICATION_MESSAGE,
    UNSUPPORTED_DOCUMENT_MESSAGE,
)
from app.bot.utils import split_telegram_text
from app.config import Settings
from app.documents.exceptions import (
    DocumentProcessingError,
    DocumentTooLargeError,
    EmptyDocumentError,
    UnsupportedDocumentError,
)
from app.documents.schemas import ProcessedDocument
from app.services.analysis_service import AnalysisService, format_analysis, format_history
from app.services.company_profile_service import CompanyProfileService
from app.services.consultant_service import ConsultantService
from app.services.document_service import DocumentService
from app.services.notification_service import NotificationService
from app.services.tender_catalog_service import TenderCatalogService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)


def register_menu_handlers(router: Router) -> None:
    @router.message(F.text == COMPANY_BUTTON)
    async def request_company_description(message: Message, state: FSMContext) -> None:
        await state.set_state(CompanyProfileState.waiting_for_description)
        await message.answer(COMPANY_PROMPT)

    @router.message(CompanyProfileState.waiting_for_description, F.text)
    async def save_company_description(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        company_profile_service: CompanyProfileService,
    ) -> None:
        description = (message.text or "").strip()
        if not description:
            await message.answer("Опишите компанию одним сообщением.")
            return
        user = await _ensure_user(message, user_service)
        if user is None:
            return
        await company_profile_service.save_description(user.id, description)
        await state.clear()
        await message.answer(COMPANY_SAVED_MESSAGE, reply_markup=company_saved_keyboard())

    @router.message(F.text == MATCHES_BUTTON)
    async def show_matches_from_menu(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        tender_catalog_service: TenderCatalogService,
    ) -> None:
        await state.clear()
        await _show_matches(message, user_service, tender_catalog_service)

    @router.callback_query(F.data == "matches:show")
    async def show_matches_from_callback(
        callback: CallbackQuery,
        state: FSMContext,
        user_service: UserService,
        tender_catalog_service: TenderCatalogService,
    ) -> None:
        await callback.answer()
        await state.clear()
        if isinstance(callback.message, Message):
            user = await _ensure_callback_user(callback, user_service)
            if user is not None:
                await _show_matches(
                    callback.message,
                    user_service,
                    tender_catalog_service,
                    user_id=user.id,
                )

    @router.callback_query(F.data.startswith("tender:analyze:"))
    async def analyze_demo_tender(
        callback: CallbackQuery,
        state: FSMContext,
        user_service: UserService,
        tender_catalog_service: TenderCatalogService,
        document_service: DocumentService,
        analysis_service: AnalysisService,
        settings: Settings,
    ) -> None:
        await callback.answer()
        message = callback.message
        if not isinstance(message, Message):
            return
        external_id = (callback.data or "").removeprefix("tender:analyze:")
        candidate = await tender_catalog_service.get_candidate(external_id)
        user = await _ensure_callback_user(callback, user_service)
        if candidate is None:
            await message.answer("Этот тестовый тендер больше недоступен. Откройте список ещё раз.")
            return
        if user is None:
            return
        tender = await tender_catalog_service.save_selected(user.id, candidate)
        await _run_analysis(
            message,
            state,
            user_id=user.id,
            processed_factory=lambda: document_service.ingest_text(
                user_id=user.id,
                filename="demo_razrabotka_korporativnogo_sayta.txt",
                text=candidate.document_text,
                tender_id=tender.id,
            ),
            settings=settings,
            analysis_service=analysis_service,
            completion_markup=analysis_complete_keyboard(),
        )

    @router.message(F.text == ANALYZE_BUTTON)
    async def request_document(message: Message, state: FSMContext) -> None:
        await state.set_state(DocumentAnalysisState.waiting_for_document)
        await message.answer(ANALYSIS_MESSAGE)

    @router.message(F.text == CONSULTANT_BUTTON)
    async def request_question(message: Message, state: FSMContext) -> None:
        await state.set_state(ConsultantState.waiting_for_question)
        await message.answer(CONSULTANT_MESSAGE)

    @router.callback_query(F.data == "consultant:ask")
    async def request_question_from_callback(
        callback: CallbackQuery, state: FSMContext
    ) -> None:
        await callback.answer()
        await state.set_state(ConsultantState.waiting_for_question)
        if isinstance(callback.message, Message):
            await callback.message.answer(CONSULTANT_PROMPT)

    @router.message(F.text == NOTIFICATIONS_BUTTON)
    async def show_notifications_from_menu(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        notification_service: NotificationService,
    ) -> None:
        await state.clear()
        await _show_notifications(message, user_service, notification_service)

    @router.callback_query(F.data == "notifications:show")
    async def show_notifications_from_callback(
        callback: CallbackQuery,
        state: FSMContext,
        user_service: UserService,
        notification_service: NotificationService,
    ) -> None:
        await callback.answer()
        await state.clear()
        if isinstance(callback.message, Message):
            user = await _ensure_callback_user(callback, user_service)
            if user is not None:
                await _show_notifications(
                    callback.message,
                    user_service,
                    notification_service,
                    user_id=user.id,
                )

    @router.callback_query(F.data == "notifications:test")
    async def send_test_notification(callback: CallbackQuery) -> None:
        await callback.answer("Тестовое уведомление отправлено")
        if isinstance(callback.message, Message):
            await callback.message.answer(TEST_NOTIFICATION_MESSAGE)

    @router.callback_query(F.data.startswith("notifications:toggle:"))
    async def toggle_notifications(
        callback: CallbackQuery,
        user_service: UserService,
        notification_service: NotificationService,
    ) -> None:
        await callback.answer()
        if not isinstance(callback.message, Message):
            return
        user = await _ensure_callback_user(callback, user_service)
        if user is None:
            return
        enabled = (callback.data or "").endswith(":on")
        await notification_service.set_enabled(user.id, enabled)
        status = "да" if enabled else "нет"
        await callback.message.edit_text(
            NOTIFICATIONS_MESSAGE.format(status=status),
            reply_markup=notifications_keyboard(enabled),
        )

    @router.message(F.text == HISTORY_BUTTON)
    async def show_history(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        analysis_service: AnalysisService,
    ) -> None:
        await state.clear()
        user = await _ensure_user(message, user_service)
        if user is None:
            return
        analyses = await analysis_service.list_recent(user.id)
        await message.answer(format_history(analyses))

    @router.message(F.text == HOW_IT_WORKS_BUTTON)
    async def show_how_it_works(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer(HOW_IT_WORKS_MESSAGE)

    @router.message(DocumentAnalysisState.waiting_for_document, F.text)
    async def analyze_pasted_specification(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        document_service: DocumentService,
        analysis_service: AnalysisService,
        settings: Settings,
    ) -> None:
        text = (message.text or "").strip()
        if not text:
            await message.answer(NO_SPEC_TEXT_MESSAGE)
            return
        user = await _ensure_user(message, user_service)
        if user is None:
            return
        await _run_analysis(
            message,
            state,
            user_id=user.id,
            processed_factory=lambda: document_service.ingest_text(user_id=user.id, text=text),
            settings=settings,
            analysis_service=analysis_service,
            completion_markup=analysis_complete_keyboard(),
        )

    @router.message(F.document)
    async def analyze_uploaded_document(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        document_service: DocumentService,
        analysis_service: AnalysisService,
        settings: Settings,
    ) -> None:
        telegram_document = message.document
        if telegram_document is None:
            return
        if (
            telegram_document.file_size is not None
            and telegram_document.file_size > settings.max_file_size_bytes
        ):
            await message.answer(f"❌ Файл больше допустимого размера {settings.max_file_size_mb} МБ.")
            return
        user = await _ensure_user(message, user_service)
        if user is None:
            return
        filename = telegram_document.file_name or "document"
        buffer = BytesIO()
        await message.bot.download(telegram_document, destination=buffer)
        data = buffer.getvalue()

        async def ingest() -> ProcessedDocument:
            return await document_service.ingest_bytes(
                user_id=user.id,
                filename=filename,
                data=data,
                mime_type=telegram_document.mime_type,
            )

        await _run_analysis(
            message,
            state,
            user_id=user.id,
            processed_factory=ingest,
            settings=settings,
            analysis_service=analysis_service,
            completion_markup=analysis_complete_keyboard(),
        )

    @router.message(ConsultantState.waiting_for_question, F.text)
    async def answer_selected_consultant_question(
        message: Message,
        state: FSMContext,
        user_service: UserService,
        consultant_service: ConsultantService,
    ) -> None:
        await _answer_consultant_question(message, user_service, consultant_service)
        await state.clear()

    @router.message(F.text)
    async def answer_consultant_question(
        message: Message,
        user_service: UserService,
        consultant_service: ConsultantService,
    ) -> None:
        await _answer_consultant_question(message, user_service, consultant_service)


async def _show_matches(
    message: Message,
    user_service: UserService,
    tender_catalog_service: TenderCatalogService,
    *,
    user_id: int | None = None,
) -> None:
    if user_id is None:
        user = await _ensure_user(message, user_service)
        if user is None:
            return
        user_id = user.id
    matches = await tender_catalog_service.find_matches(user_id)
    if not matches:
        await message.answer(PROFILE_REQUIRED_MESSAGE)
        return
    for index, match in enumerate(matches):
        prefix = "🎯 Подходящие тендеры\n\n" if index == 0 else ""
        await message.answer(
            prefix + _format_match(match), reply_markup=tender_keyboard(match.tender.external_id)
        )


async def _show_notifications(
    message: Message,
    user_service: UserService,
    notification_service: NotificationService,
    *,
    user_id: int | None = None,
) -> None:
    if user_id is None:
        user = await _ensure_user(message, user_service)
        if user is None:
            return
        user_id = user.id
    enabled = await notification_service.is_enabled(user_id)
    await message.answer(
        NOTIFICATIONS_MESSAGE.format(status="да" if enabled else "нет"),
        reply_markup=notifications_keyboard(enabled),
    )


async def _answer_consultant_question(
    message: Message, user_service: UserService, consultant_service: ConsultantService
) -> None:
    question = (message.text or "").strip()
    if not question:
        return
    user = await _ensure_user(message, user_service)
    if user is None:
        return
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        answer = await consultant_service.answer(user_id=user.id, question=question)
    except AIProviderConfigurationError:
        await message.answer("❌ AI-консультант не настроен. Добавьте GEMINI_API_KEY в .env.")
    except AIProviderTimeoutError:
        await message.answer("⏳ Ответ AI занял слишком много времени. Попробуйте ещё раз.")
    except AIProviderError:
        user_id = message.from_user.id if message.from_user else "unknown"
        logger.warning("Consultant request failed for user_id=%s", user_id)
        await message.answer("❌ Не удалось получить ответ AI-консультанта. Попробуйте ещё раз позже.")
    else:
        for chunk in split_telegram_text(answer):
            await message.answer(chunk)


async def _ensure_user(message: Message, user_service: UserService):
    telegram_user = message.from_user
    if telegram_user is None:
        logger.warning("Received a message without a Telegram user")
        return None
    return await user_service.ensure_telegram_user(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
    )


async def _ensure_callback_user(callback: CallbackQuery, user_service: UserService):
    telegram_user = callback.from_user
    if telegram_user is None:
        logger.warning("Received a callback without a Telegram user")
        return None
    return await user_service.ensure_telegram_user(
        telegram_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name,
    )


async def _run_analysis(
    message: Message,
    state: FSMContext,
    *,
    user_id: int,
    processed_factory: Callable[[], Awaitable[ProcessedDocument]],
    settings: Settings,
    analysis_service: AnalysisService,
    completion_markup=None,
) -> None:
    await message.answer(ANALYSIS_STARTED_MESSAGE)
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        processed = await processed_factory()
        analysis = await analysis_service.analyze(processed)
    except DocumentTooLargeError:
        await message.answer(f"❌ Файл больше допустимого размера {settings.max_file_size_mb} МБ.")
        return
    except UnsupportedDocumentError:
        await message.answer(UNSUPPORTED_DOCUMENT_MESSAGE)
        return
    except EmptyDocumentError:
        await message.answer(EMPTY_DOCUMENT_MESSAGE)
        return
    except DocumentProcessingError:
        await message.answer(DOCUMENT_READ_ERROR_MESSAGE)
        return
    except AIProviderConfigurationError:
        await message.answer("❌ Анализ документов не настроен. Добавьте GEMINI_API_KEY в .env.")
        return
    except AIProviderTimeoutError:
        await message.answer("⏳ Разбор документа занял слишком много времени. Попробуйте ещё раз.")
        return
    except AIProviderError:
        logger.warning("Document analysis failed for user_id=%s", user_id)
        await message.answer("❌ Не удалось проанализировать документ. Попробуйте ещё раз позже.")
        return
    except Exception:
        logger.exception("Unexpected document analysis failure for user_id=%s", user_id)
        await message.answer(DOCUMENT_READ_ERROR_MESSAGE)
        return

    await state.clear()
    rendered_chunks = split_telegram_text(format_analysis(processed, analysis))
    for index, chunk in enumerate(rendered_chunks):
        markup = completion_markup if index == len(rendered_chunks) - 1 else None
        await message.answer(chunk, reply_markup=markup)


def _format_match(match) -> str:
    amount = f"{match.tender.amount:,.0f}".replace(",", " ")
    lines = [
        match.tender.title,
        f"{amount} ₸",
        f"Соответствие {match.score}%",
        f"Заказчик: {match.tender.customer}",
        match.tender.deadline_label,
    ]
    if match.matched_keywords:
        lines.append("Совпадения: " + ", ".join(match.matched_keywords))
    return "\n".join(lines)
