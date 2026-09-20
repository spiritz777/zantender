"""AI provider abstractions and implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.ai.providers.base import AIProvider
    from app.config import Settings


def create_ai_provider(settings: "Settings") -> "AIProvider":
    """Lazily load the concrete provider so test doubles need no SDK import."""
    from app.ai.service import create_ai_provider as create_provider

    return create_provider(settings)


__all__ = ["create_ai_provider"]
