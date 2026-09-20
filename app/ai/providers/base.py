"""Provider contract used by application services instead of SDK calls."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class AIProvider(ABC):
    """Minimal asynchronous interface shared by all AI implementations."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, *, system_instruction: str | None = None
    ) -> str:
        """Generate a text response from the supplied prompt."""

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[SchemaT],
        *,
        system_instruction: str | None = None,
    ) -> SchemaT:
        """Generate and validate a response against a Pydantic model."""

