"""Provider-neutral tender data used by matching and Telegram UX."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TenderCandidate:
    external_id: str
    title: str
    customer: str
    amount: Decimal
    deadline_label: str
    keywords: tuple[str, ...]
    document_text: str
    source: str = "demo"
