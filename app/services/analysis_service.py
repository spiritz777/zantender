"""Run AI analysis on an ingested document and format the result."""

from __future__ import annotations

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.ai.prompts.analysis import ANALYSIS_SYSTEM_INSTRUCTION
from app.ai.providers.base import AIProvider
from app.ai.schemas import TenderAnalysisResult
from app.config import Settings
from app.database.database import session_scope
from app.database.models import Analysis, Document
from app.documents.schemas import ProcessedDocument


class AnalysisService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        self._session_factory = session_factory
        self._ai_provider = ai_provider
        self._settings = settings

    async def analyze(self, processed: ProcessedDocument) -> Analysis:
        context = _join_chunks(processed, self._settings.analysis_context_max_chars)
        prompt = (
            f"Файл: {processed.filename}\n"
            f"Страниц: {processed.page_count}\n\n"
            f"Текст документа:\n{context}"
        )
        result = await self._ai_provider.generate_structured(
            prompt,
            TenderAnalysisResult,
            system_instruction=ANALYSIS_SYSTEM_INSTRUCTION,
        )
        return await asyncio.to_thread(self._save, processed, result)

    async def list_recent(self, user_id: int, limit: int = 10) -> list[Analysis]:
        return await asyncio.to_thread(self._list_recent, user_id, limit)

    def _save(
        self, processed: ProcessedDocument, result: TenderAnalysisResult
    ) -> Analysis:
        with session_scope(self._session_factory) as session:
            document = session.get(Document, processed.document_id)
            if document is None:
                raise ValueError("Document does not exist.")
            analysis = Analysis(
                user_id=document.user_id,
                document_id=document.id,
                score=result.score,
                recommendation=result.recommendation,
                result_json=result.model_dump(),
            )
            session.add(analysis)
            session.flush()
            session.refresh(analysis)
            return analysis

    def _list_recent(self, user_id: int, limit: int) -> list[Analysis]:
        with session_scope(self._session_factory) as session:
            return list(
                session.scalars(
                    select(Analysis)
                    .options(selectinload(Analysis.document))
                    .where(Analysis.user_id == user_id)
                    .order_by(Analysis.created_at.desc(), Analysis.id.desc())
                    .limit(limit)
                ).all()
            )


def format_analysis(processed: ProcessedDocument, analysis: Analysis) -> str:
    data = TenderAnalysisResult.model_validate(analysis.result_json)
    title = data.title or processed.filename
    customer = data.customer or "не указан в документе"
    return (
        f"📄 Анализ: {title}\n"
        f"Заказчик: {customer}\n"
        f"Файл: {processed.filename} · страниц: {processed.page_count}\n\n"
        f"📌 Кратко\n{data.summary}\n\n"
        f"📋 Требования\n{_bullets(data.requirements)}\n\n"
        f"📎 Документы для заявки\n{_bullets(data.required_documents)}\n\n"
        f"⏰ Сроки\n{_bullets(data.deadlines)}\n\n"
        f"⚠️ Риски\n{_bullets(data.risks)}\n\n"
        f"📊 Оценка документа: {data.score}/100\n"
        f"{data.recommendation}\n\n"
        "⚠️ Это аналитическая рекомендация, а не юридическое заключение."
    )


def format_history(analyses: list[Analysis]) -> str:
    if not analyses:
        return (
            "📃 Мои анализы\n\n"
            "Пока сохранённых разборов нет. Отправьте PDF, DOCX или текст спецификации."
        )
    lines = ["📃 Мои анализы\n"]
    for analysis in analyses:
        filename = analysis.document.filename if analysis.document else "документ"
        stamped = _format_timestamp(analysis.created_at)
        score = f"{analysis.score}/100" if analysis.score is not None else "без оценки"
        recommendation = (analysis.recommendation or "").strip()
        if len(recommendation) > 180:
            recommendation = recommendation[:177].rstrip() + "..."
        lines.append(f"• {stamped} — {filename} ({score})\n  {recommendation}")
    return "\n\n".join(lines)


def _join_chunks(processed: ProcessedDocument, max_chars: int) -> str:
    parts: list[str] = []
    used = 0
    for chunk in processed.chunks:
        remaining = max_chars - used
        if remaining <= 0:
            break
        text = chunk.text[:remaining]
        parts.append(text)
        used += len(text)
    return "\n\n".join(parts)


def _bullets(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return "— не найдено в документе"
    return "\n".join(f"• {item}" for item in cleaned)


def _format_timestamp(value: datetime) -> str:
    return value.strftime("%d.%m.%Y %H:%M")
