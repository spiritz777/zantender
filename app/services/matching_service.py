"""Transparent deterministic matching for the local MVP."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.database.models import CompanyProfile
from app.tenders.schemas import TenderCandidate


@dataclass(frozen=True, slots=True)
class TenderMatch:
    tender: TenderCandidate
    score: int
    matched_keywords: tuple[str, ...]


class MatchingService:
    def match(
        self, profile: CompanyProfile, tenders: list[TenderCandidate]
    ) -> list[TenderMatch]:
        profile_words = _normalise_words(
            f"{profile.description or ''} {profile.industry or ''}"
        )
        matches = [self._score(tender, profile_words) for tender in tenders]
        return sorted(matches, key=lambda match: match.score, reverse=True)

    def _score(self, tender: TenderCandidate, profile_words: set[str]) -> TenderMatch:
        tender_words = {_normalise_word(word) for word in tender.keywords}
        overlap = tuple(sorted(word for word in tender_words if word in profile_words))
        if len(overlap) >= 2:
            score = 91
        elif len(overlap) == 1:
            score = 63
        else:
            score = 15
        return TenderMatch(tender=tender, score=score, matched_keywords=overlap)


def _normalise_words(text: str) -> set[str]:
    return {_normalise_word(word) for word in re.findall(r"[a-zа-яё]+", text.lower())}


def _normalise_word(word: str) -> str:
    word = word.lower().replace("ё", "е")
    if word.startswith("сайт"):
        return "сайт"
    if word.startswith("разработ"):
        return "разработка"
    return word
