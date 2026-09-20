from app.bot.utils import MAX_TELEGRAM_MESSAGE_LENGTH, split_telegram_text


def test_telegram_response_is_split_at_spaces() -> None:
    response = ("слово " * 1000).strip()

    chunks = split_telegram_text(response)

    assert len(chunks) == 2
    assert all(len(chunk) <= MAX_TELEGRAM_MESSAGE_LENGTH for chunk in chunks)
    assert " ".join(chunks) == response
