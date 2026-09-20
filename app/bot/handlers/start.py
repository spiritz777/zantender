"""The /start command handler."""

from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.main_menu import main_menu
from app.bot.texts import START_MESSAGE
from app.services.user_service import UserService


logger = logging.getLogger(__name__)


def register_start_handler(router: Router) -> None:
    @router.message(CommandStart())
    async def start_command(
        message: Message, state: FSMContext, user_service: UserService
    ) -> None:
        telegram_user = message.from_user
        if telegram_user is None:
            logger.warning("Received /start without a Telegram user")
            return

        await user_service.ensure_telegram_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
        )
        await state.clear()
        await message.answer(START_MESSAGE, reply_markup=main_menu())
