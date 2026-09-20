"""Local bootstrap entry point for ZanTender AI."""

from __future__ import annotations

import asyncio
import logging

from app.config import get_settings
from app.database.database import get_session_factory, init_database
from app.logging_config import configure_logging
from app.services.user_service import UserService
from app.utils.single_instance import AnotherInstanceRunningError, SingleInstanceLock


async def main() -> None:
    """Prepare local infrastructure and start the Telegram bot when configured."""
    settings = get_settings()
    configure_logging(settings)
    logger = logging.getLogger(__name__)

    engine = init_database(settings)
    logger.info("Local infrastructure is ready")
    if not settings.bot_token:
        logger.warning("BOT_TOKEN is not configured; Telegram polling is not started")
        return

    from app.bot.application import run_polling

    lock = SingleInstanceLock(settings.data_dir / "zantender_bot.lock")
    try:
        lock.acquire()
    except AnotherInstanceRunningError:
        logger.error("Bot is already running locally. Stop the other copy first.")
        return

    try:
        await run_polling(settings, UserService(get_session_factory(engine)))
    except RuntimeError as error:
        logger.error("Bot stopped: %s", error)
    finally:
        lock.release()


if __name__ == "__main__":
    asyncio.run(main())
