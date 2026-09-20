"""AI provider factory used by future application services."""

from app.ai.providers.base import AIProvider
from app.ai.providers.demo import DemoAIProvider
from app.ai.providers.gemini import GeminiProvider
from app.config import Settings


def create_ai_provider(settings: Settings) -> AIProvider:
    """Create the local deterministic demo provider or the configured Gemini one."""
    if settings.demo_mode:
        return DemoAIProvider()
    return GeminiProvider.from_settings(settings)
