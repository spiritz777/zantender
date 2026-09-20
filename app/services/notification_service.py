"""Notification preferences for the demo and a future live tender feed."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.database import session_scope
from app.database.models import NotificationPreference


class NotificationService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def is_enabled(self, user_id: int) -> bool:
        return await asyncio.to_thread(self._is_enabled, user_id)

    async def set_enabled(self, user_id: int, enabled: bool) -> bool:
        return await asyncio.to_thread(self._set_enabled, user_id, enabled)

    def _is_enabled(self, user_id: int) -> bool:
        with session_scope(self._session_factory) as session:
            preference = session.scalar(
                select(NotificationPreference).where(NotificationPreference.user_id == user_id)
            )
            return preference.enabled if preference is not None else True

    def _set_enabled(self, user_id: int, enabled: bool) -> bool:
        with session_scope(self._session_factory) as session:
            preference = session.scalar(
                select(NotificationPreference).where(NotificationPreference.user_id == user_id)
            )
            if preference is None:
                preference = NotificationPreference(user_id=user_id, enabled=enabled)
                session.add(preference)
            else:
                preference.enabled = enabled
            return enabled
