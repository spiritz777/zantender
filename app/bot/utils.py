"""Telegram-specific presentation helpers."""

MAX_TELEGRAM_MESSAGE_LENGTH = 4096


def split_telegram_text(text: str) -> list[str]:
    """Split a long response on a natural boundary accepted by Telegram."""
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    while len(text) > MAX_TELEGRAM_MESSAGE_LENGTH:
        candidate = text[:MAX_TELEGRAM_MESSAGE_LENGTH]
        boundary = max(candidate.rfind("\n"), candidate.rfind(" "))
        if boundary <= 0:
            boundary = MAX_TELEGRAM_MESSAGE_LENGTH
        chunks.append(text[:boundary].strip())
        text = text[boundary:].strip()
    chunks.append(text)
    return chunks
