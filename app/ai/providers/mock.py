"""Deterministic provider for unit tests; it never calls an external API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.ai.providers.base import AIProvider, SchemaT


class MockAIProvider(AIProvider):
    def __init__(
        self, text_response: str = "Mock response", structured_response: Any = None
    ) -> None:
        self.text_response = text_response
        self.structured_response = structured_response
        self.requests: list[tuple[str, str | None]] = []

    async def generate_text(
        self, prompt: str, *, system_instruction: str | None = None
    ) -> str:
        self.requests.append((prompt, system_instruction))
        return self.text_response

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[SchemaT],
        *,
        system_instruction: str | None = None,
    ) -> SchemaT:
        self.requests.append((prompt, system_instruction))
        value = self.structured_response
        if isinstance(value, response_schema):
            return value
        return response_schema.model_validate(value)
