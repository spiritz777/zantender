"""Company profile persistence kept outside Telegram handlers."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.database import session_scope
from app.database.models import CompanyProfile


class CompanyProfileService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def save_description(self, user_id: int, description: str) -> CompanyProfile:
        return await asyncio.to_thread(self._save_description, user_id, description)

    async def get(self, user_id: int) -> CompanyProfile | None:
        return await asyncio.to_thread(self._get, user_id)

    def _save_description(self, user_id: int, description: str) -> CompanyProfile:
        clean_description = description.strip()
        with session_scope(self._session_factory) as session:
            profile = session.scalar(
                select(CompanyProfile).where(CompanyProfile.user_id == user_id)
            )
            if profile is None:
                profile = CompanyProfile(
                    user_id=user_id,
                    company_name="Моя компания",
                    description=clean_description,
                    industry=_detect_industry(clean_description),
                )
                session.add(profile)
                session.flush()
            else:
                profile.description = clean_description
                profile.industry = _detect_industry(clean_description)
            return profile

    def _get(self, user_id: int) -> CompanyProfile | None:
        with session_scope(self._session_factory) as session:
            return session.scalar(
                select(CompanyProfile).where(CompanyProfile.user_id == user_id)
            )


def _detect_industry(description: str) -> str:
    lowered = description.lower()
    if any(word in lowered for word in ("сайт", "веб", "web", "разработк")):
        return "Разработка сайтов и цифровых продуктов"
    return "Не указана"
