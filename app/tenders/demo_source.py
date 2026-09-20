"""Curated tender feed for the offline ZanTender presentation scenario."""

from __future__ import annotations

from decimal import Decimal

from app.tenders.schemas import TenderCandidate


class DemoTenderSource:
    """Static local data; replace this class with a TenderSource API adapter later."""

    async def list_open_tenders(self) -> list[TenderCandidate]:
        return [
            TenderCandidate(
                external_id="demo-corporate-website-001",
                title="Разработка корпоративного сайта",
                customer="АО «ZanDemo»",
                amount=Decimal("2450000"),
                deadline_label="Приём заявок: 10 рабочих дней",
                keywords=("разработка", "сайт", "веб", "дизайн", "cms"),
                document_text=(
                    "Техническая спецификация\n\n"
                    "Предмет закупки: разработка корпоративного сайта для АО «ZanDemo».\n"
                    "Цель: создать современный адаптивный сайт с CMS, каталогом услуг и "
                    "формой обратной связи.\n\n"
                    "Требования: UX/UI-дизайн, адаптивная вёрстка, backend-разработка, "
                    "административная панель CMS, базовая SEO-подготовка и обучение редактора.\n"
                    "Подтвердите портфолио аналогичных веб-проектов и состав команды.\n\n"
                    "Бюджет: 2 450 000 ₸. Срок подачи заявки: 10 рабочих дней. "
                    "Срок реализации: 90 календарных дней."
                ),
            ),
            TenderCandidate(
                external_id="demo-office-furniture-002",
                title="Поставка офисной мебели",
                customer="КГУ «Городской сервис»",
                amount=Decimal("1800000"),
                deadline_label="Приём заявок: 7 рабочих дней",
                keywords=("мебель", "поставка", "офис", "столы", "кресла"),
                document_text="Демо-документ закупки офисной мебели.",
            ),
            TenderCandidate(
                external_id="demo-video-003",
                title="Производство презентационного видеоролика",
                customer="ТОО «QazMedia»",
                amount=Decimal("950000"),
                deadline_label="Приём заявок: 12 рабочих дней",
                keywords=("видео", "съёмка", "монтаж", "ролик", "продакшн"),
                document_text="Демо-документ закупки услуг видеопроизводства.",
            ),
        ]
