from app.bot.keyboards.main_menu import (
    ANALYZE_BUTTON,
    COMPANY_BUTTON,
    CONSULTANT_BUTTON,
    HISTORY_BUTTON,
    HOW_IT_WORKS_BUTTON,
    MATCHES_BUTTON,
    NOTIFICATIONS_BUTTON,
    main_menu,
)


def test_main_menu_has_all_mvp_sections() -> None:
    keyboard = main_menu()

    assert [[button.text for button in row] for row in keyboard.keyboard] == [
        [COMPANY_BUTTON, MATCHES_BUTTON],
        [ANALYZE_BUTTON, CONSULTANT_BUTTON],
        [NOTIFICATIONS_BUTTON, HISTORY_BUTTON],
        [HOW_IT_WORKS_BUTTON],
    ]
