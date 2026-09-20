import asyncio

from pydantic import BaseModel

from app.ai.providers.mock import MockAIProvider


class TenderAnswer(BaseModel):
    recommendation: str
    score: int


def test_mock_provider_returns_text_without_network() -> None:
    provider = MockAIProvider(text_response="Готово")

    response = asyncio.run(provider.generate_text("Проверь документ"))

    assert response == "Готово"
    assert provider.requests == [("Проверь документ", None)]


def test_mock_provider_validates_structured_response() -> None:
    provider = MockAIProvider(
        structured_response={"recommendation": "Участвовать", "score": 82}
    )

    response = asyncio.run(
        provider.generate_structured("Оцени тендер", TenderAnswer)
    )

    assert response == TenderAnswer(recommendation="Участвовать", score=82)
