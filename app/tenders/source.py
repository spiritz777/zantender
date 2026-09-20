"""The narrow boundary a future tender API integration must implement."""

from __future__ import annotations

from typing import Protocol

from app.tenders.schemas import TenderCandidate


class TenderSource(Protocol):
    async def list_open_tenders(self) -> list[TenderCandidate]:
        """Return currently available tenders in the provider-neutral format."""
