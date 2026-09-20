"""Local bootstrap entry point for ZanTender AI."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.config import get_settings
from app.database.database import get_session_factory, init_database
from app.logging_config import configure_logging
from app.services.user_service import UserService
from app.utils.single_instance import AnotherInstanceRunningError, SingleInstanceLock


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Dummy health check HTTP handler for cloud platforms like Render."""

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format: str, *args: object) -> None:
        pass


def start_health_check_server(logger: logging.Logger) -> None:
    """Start a lightweight HTTP server if PORT environment variable is present."""
    port_str = os.environ.get("PORT")
    if not port_str:
        return
    try:
        port = int(port_str)
    except ValueError:
        return

    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logger.info("Health check server listening on 0.0.0.0:%d", port)
    except Exception as exc:
        logger.warning("Failed to start health check server: %s", exc)


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

    start_health_check_server(logger)

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

