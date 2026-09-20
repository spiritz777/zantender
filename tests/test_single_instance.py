import pytest

from app.utils.single_instance import AnotherInstanceRunningError, SingleInstanceLock


def test_second_local_instance_is_rejected(tmp_path) -> None:
    first = SingleInstanceLock(tmp_path / "zantender.lock")
    second = SingleInstanceLock(tmp_path / "zantender.lock")
    first.acquire()
    try:
        with pytest.raises(AnotherInstanceRunningError):
            second.acquire()
    finally:
        first.release()
