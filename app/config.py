"""Environment-backed application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """Configuration loaded from environment variables and an optional .env."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    bot_token: str | None = Field(default=None, validation_alias="BOT_TOKEN")
    gemini_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "AI_API_KEY"),
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        validation_alias=AliasChoices("GEMINI_MODEL", "AI_MODEL"),
    )
    gemini_timeout_seconds: PositiveInt = Field(
        default=60, validation_alias="GEMINI_TIMEOUT_SECONDS"
    )
    demo_mode: bool = Field(default=True, validation_alias="DEMO_MODE")
    database_url: str = Field(
        default="sqlite:///./data/zantender.db", validation_alias="DATABASE_URL"
    )
    max_file_size_mb: PositiveInt = Field(
        default=20, validation_alias="MAX_FILE_SIZE_MB"
    )
    chunk_size_chars: PositiveInt = Field(
        default=6000, validation_alias="CHUNK_SIZE_CHARS"
    )
    analysis_context_max_chars: PositiveInt = Field(
        default=24000, validation_alias="ANALYSIS_CONTEXT_MAX_CHARS"
    )

    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    @property
    def uploads_dir(self) -> Path:
        return PROJECT_ROOT / "uploads"

    @property
    def logs_dir(self) -> Path:
        return PROJECT_ROOT / "logs"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    def create_local_directories(self) -> None:
        """Create only directories owned by this local MVP."""
        for directory in (self.data_dir, self.uploads_dir, self.logs_dir):
            directory.mkdir(parents=True, exist_ok=True)
        self._create_sqlite_parent_directory()

    def _create_sqlite_parent_directory(self) -> None:
        """Ensure the configured relative SQLite database has a parent folder."""
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            return
        database_path = self.database_url.removeprefix(prefix)
        if not database_path or database_path == ":memory:":
            return
        path = Path(database_path)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
