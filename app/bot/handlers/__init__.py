"""Register Telegram handlers."""

from aiogram import Router

from app.bot.handlers.menu import register_menu_handlers
from app.bot.handlers.start import register_start_handler


router = Router(name="main")
register_start_handler(router)
register_menu_handlers(router)

