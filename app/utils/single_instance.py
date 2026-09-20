"""Cross-platform process lock for local polling."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import BinaryIO

if sys.platform == "win32":
    import msvcrt
else:
    msvcrt = None

try:
    import fcntl
except ImportError:
    fcntl = None


class AnotherInstanceRunningError(RuntimeError):
    """Raised when another local ZanTender polling process owns the lock."""


class SingleInstanceLock:
    """An OS-level lock released automatically if the process exits unexpectedly."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path
        self._file: BinaryIO | None = None

    def acquire(self) -> None:
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._lock_path.exists() or self._lock_path.stat().st_size == 0:
            self._lock_path.write_bytes(b"0")
        lock_file = self._lock_path.open("r+b")

        try:
            if msvcrt is not None:
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            elif fcntl is not None:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError) as error:
            lock_file.close()
            raise AnotherInstanceRunningError(
                "Another ZanTender bot process is already running."
            ) from error

        self._file = lock_file

    def release(self) -> None:
        if self._file is None:
            return
        try:
            if msvcrt is not None:
                self._file.seek(0)
                msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
            elif fcntl is not None:
                fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        finally:
            self._file.close()
            self._file = None

