"""Domain exceptions for AI operations.

Exception messages are intentionally generic: prompts, document content and
credentials must never be exposed to users or logs through an exception.
"""


class AIProviderError(RuntimeError):
    """Base exception for a failed AI provider operation."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when a provider is used without mandatory configuration."""


class AIProviderResponseError(AIProviderError):
    """Raised when the provider returns an unusable response."""


class AIProviderTimeoutError(AIProviderError):
    """Raised when an AI request exceeds the configured timeout."""

