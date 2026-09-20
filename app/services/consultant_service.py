"""Answer procurement questions, using the latest document when available."""

from __future__ import annotations

from app.ai.prompts.consultant import CONSULTANT_SYSTEM_INSTRUCTION
from app.ai.providers.base import AIProvider
from app.config import Settings
from app.services.document_service import DocumentService


class ConsultantService:
    def __init__(
        self,
        ai_provider: AIProvider,
        document_service: DocumentService,
        settings: Settings,
    ) -> None:
        self._ai_provider = ai_provider
        self._document_service = document_service
        self._settings = settings

    async def answer(self, *, user_id: int, question: str) -> str:
        context = await self._document_service.get_latest_context(
            user_id, self._settings.analysis_context_max_chars
        )
        return await self._ai_provider.generate_text(
            build_consultant_prompt(question, context),
            system_instruction=CONSULTANT_SYSTEM_INSTRUCTION,
        )


def build_consultant_prompt(
    question: str, document_context: tuple[str, str] | None
) -> str:
    if document_context is None:
        return (
            "Документ пользователя не загружен. Ответь на общий вопрос по закупкам.\n\n"
            f"Вопрос:\n{question}"
        )
    filename, text = document_context
    return (
        f"Вопрос пользователя:\n{question}\n\n"
        f"Ниже текст последнего документа пользователя ({filename}). "
        "Для фактов этого тендера используй только его.\n\n"
        f"{text}"
    )
