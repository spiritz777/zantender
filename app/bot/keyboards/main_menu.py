"""Persistent and contextual keyboards for the demo-first Telegram UX."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


COMPANY_BUTTON = "🏢 Настроить компанию"
MATCHES_BUTTON = "🎯 Подходящие тендеры"
ANALYZE_BUTTON = "📄 Анализ документа"
CONSULTANT_BUTTON = "⚖️ AI-консультант"
NOTIFICATIONS_BUTTON = "🔔 Мои уведомления"
HISTORY_BUTTON = "📚 История анализов"
HOW_IT_WORKS_BUTTON = "ℹ️ Как это работает"

# Kept as a compatibility alias for the previous menu API.
PROSPECT_BUTTON = MATCHES_BUTTON


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=COMPANY_BUTTON), KeyboardButton(text=MATCHES_BUTTON)],
            [KeyboardButton(text=ANALYZE_BUTTON), KeyboardButton(text=CONSULTANT_BUTTON)],
            [KeyboardButton(text=NOTIFICATIONS_BUTTON), KeyboardButton(text=HISTORY_BUTTON)],
            [KeyboardButton(text=HOW_IT_WORKS_BUTTON)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )


def company_saved_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Подходящие тендеры", callback_data="matches:show")]
        ]
    )


def tender_keyboard(external_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Анализировать", callback_data=f"tender:analyze:{external_id}"
                )
            ]
        ]
    )


def analysis_complete_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Задать вопрос", callback_data="consultant:ask")],
            [InlineKeyboardButton(text="🔔 Мои уведомления", callback_data="notifications:show")],
        ]
    )


def notifications_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    toggle_text = "🔕 Выключить уведомления" if enabled else "🔔 Включить уведомления"
    toggle_value = "off" if enabled else "on"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🧪 Тестовое уведомление", callback_data="notifications:test")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"notifications:toggle:{toggle_value}")],
        ]
    )
