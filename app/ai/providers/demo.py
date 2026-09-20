"""Offline deterministic AI responses used by the presentation demo."""

from __future__ import annotations

from app.ai.providers.base import AIProvider, SchemaT


class DemoAIProvider(AIProvider):
    """Make the complete MVP flow work without an external AI key or network."""

    async def generate_text(
        self, prompt: str, *, system_instruction: str | None = None
    ) -> str:
        question = prompt.lower()
        if "почему этот тендер мне подходит" in question:
            return (
                "Этот тендер подходит, потому что в нём требуется разработка "
                "корпоративного сайта: проектирование, дизайн, адаптивная вёрстка "
                "и запуск CMS. Это напрямую совпадает с профилем компании, которая "
                "занимается разработкой сайтов. Срок в 90 дней реалистичен для команды "
                "с подтверждённым опытом, поэтому matching оценивает соответствие в 91%."
            )
        return (
            "В демо-режиме я отвечаю на основе выбранной тендерной документации. "
            "Задайте вопрос о требованиях, сроках, рисках или соответствии вашей компании."
        )

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[SchemaT],
        *,
        system_instruction: str | None = None,
    ) -> SchemaT:
        return response_schema.model_validate(
            {
                "title": "Разработка корпоративного сайта",
                "customer": "АО «ZanDemo»",
                "summary": (
                    "Нужно спроектировать, разработать и запустить корпоративный "
                    "сайт с системой управления контентом."
                ),
                "requirements": [
                    "Адаптивный дизайн и вёрстка",
                    "Разработка сайта и административной панели CMS",
                    "Интеграция формы обратной связи и базовая SEO-подготовка",
                ],
                "required_documents": [
                    "Коммерческое предложение",
                    "Портфолио аналогичных веб-проектов",
                    "Сведения о команде проекта",
                ],
                "deadlines": ["Подача заявки — 10 рабочих дней", "Реализация — 90 календарных дней"],
                "risks": [
                    "Нужно подтвердить опыт похожих проектов",
                    "Важно заранее согласовать состав интеграций и контента",
                ],
                "score": 82,
                "recommendation": (
                    "Участвовать: профиль компании хорошо соответствует предмету закупки. "
                    "До подачи заявки подготовьте релевантное портфолио и план проекта."
                ),
            }
        )
