"""User persistence operations used by Telegram handlers."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.database import session_scope
from app.database.models import User


class UserService:
    """Create or update a user from an incoming Telegram profile."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self.session_factory = session_factory

    async def ensure_telegram_user(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> User:
        """Persist a Telegram user without blocking the polling event loop."""
        return await asyncio.to_thread(
            self._ensure_telegram_user, telegram_id, username, first_name
        )

    def _ensure_telegram_user(
        self, telegram_id: int, username: str | None, first_name: str | None
    ) -> User:
        with session_scope(self.session_factory) as session:
            user = session.scalar(select(User).where(User.telegram_id == telegram_id))
            if user is None:
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                )
                session.add(user)
                session.flush()
                return user

            user.username = username
            user.first_name = first_name
            return user

