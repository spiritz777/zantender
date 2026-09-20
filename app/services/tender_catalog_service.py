"""Source-independent catalogue, matching and selected-tender persistence."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.database import session_scope
from app.database.models import Tender
from app.services.company_profile_service import CompanyProfileService
from app.services.matching_service import MatchingService, TenderMatch
from app.tenders.schemas import TenderCandidate
from app.tenders.source import TenderSource


class TenderCatalogService:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        source: TenderSource,
        company_profiles: CompanyProfileService,
        matching: MatchingService,
    ) -> None:
        self._session_factory = session_factory
        self._source = source
        self._company_profiles = company_profiles
        self._matching = matching

    async def find_matches(self, user_id: int) -> list[TenderMatch]:
        profile = await self._company_profiles.get(user_id)
        if profile is None or not (profile.description or "").strip():
            return []
        return self._matching.match(profile, await self._source.list_open_tenders())

    async def get_candidate(self, external_id: str) -> TenderCandidate | None:
        return next(
            (
                tender
                for tender in await self._source.list_open_tenders()
                if tender.external_id == external_id
            ),
            None,
        )

    async def save_selected(self, user_id: int, candidate: TenderCandidate) -> Tender:
        return await asyncio.to_thread(self._save_selected, user_id, candidate)

    def _save_selected(self, user_id: int, candidate: TenderCandidate) -> Tender:
        with session_scope(self._session_factory) as session:
            tender = session.scalar(
                select(Tender).where(
                    Tender.user_id == user_id,
                    Tender.source == candidate.source,
                    Tender.external_id == candidate.external_id,
                )
            )
            if tender is None:
                tender = Tender(
                    user_id=user_id,
                    title=candidate.title,
                    customer=candidate.customer,
                    amount=Decimal(candidate.amount),
                    source=candidate.source,
                    external_id=candidate.external_id,
                )
                session.add(tender)
                session.flush()
            return tender
