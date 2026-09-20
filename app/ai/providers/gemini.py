"""Gemini Developer API provider implementation."""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.ai.exceptions import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.ai.providers.base import AIProvider, SchemaT
from app.config import Settings


class GeminiProvider(AIProvider):
    """Asynchronous Gemini client for the Google AI Developer API."""

    def __init__(self, api_key: str | None, model: str, timeout_seconds: int = 60):
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> "GeminiProvider":
        return cls(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            timeout_seconds=settings.gemini_timeout_seconds,
        )

    async def generate_text(
        self, prompt: str, *, system_instruction: str | None = None
    ) -> str:
        self._ensure_configured()
        config = types.GenerateContentConfig(system_instruction=system_instruction)
        response = await self._generate(prompt, config)
        return self._response_text(response)

    async def generate_structured(
        self,
        prompt: str,
        response_schema: type[SchemaT],
        *,
        system_instruction: str | None = None,
    ) -> SchemaT:
        self._ensure_configured()
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
        response = await self._generate(prompt, config)
        text = self._response_text(response)
        try:
            return response_schema.model_validate_json(text)
        except ValidationError as error:
            raise AIProviderResponseError(
                "Gemini returned data in an unexpected format."
            ) from error

    async def _generate(
        self, prompt: str, config: types.GenerateContentConfig
    ) -> types.GenerateContentResponse:
        try:
            async with genai.Client(api_key=self._api_key).aio as client:
                async with asyncio.timeout(self._timeout_seconds):
                    return await client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    )
        except TimeoutError as error:
            raise AIProviderTimeoutError("Gemini request timed out.") from error
        except AIProviderError:
            raise
        except Exception as error:
            raise AIProviderError("Gemini request failed.") from error

    @staticmethod
    def _response_text(response: types.GenerateContentResponse) -> str:
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise AIProviderResponseError("Gemini returned an empty response.")
        return text

    def _ensure_configured(self) -> None:
        if not self._api_key:
            raise AIProviderConfigurationError(
                "GEMINI_API_KEY must be configured before using Gemini."
            )
