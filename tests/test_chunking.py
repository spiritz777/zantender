from app.documents.chunking import chunk_pages, clean_text
from app.documents.schemas import DocumentPage


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  один\n\tдва   ") == "один два"


def test_chunk_pages_keeps_page_range_and_avoids_splitting_words() -> None:
    pages = [
        DocumentPage(page_number=1, text="один два три"),
        DocumentPage(page_number=2, text="четыре пять"),
    ]

    chunks = chunk_pages(pages, max_chars=14)

    assert [chunk.text for chunk in chunks] == ["один два три", "четыре пять"]
    assert chunks[0].page_start == 1
    assert chunks[1].page_start == 2
