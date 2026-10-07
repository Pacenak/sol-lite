from __future__ import annotations

from sol_lite.core.tasks import TaskManager


def test_background_task_retains_result():
    manager = TaskManager(max_workers=1)
    try:
        record = manager.submit("session-1", "test", lambda: {"ok": True})
        record.future.result(timeout=5)
        stored = manager.get(record.task_id)
        assert stored.status == "COMPLETED"
        assert stored.result == {"ok": True}
    finally:
        manager.shutdown()


def test_running_task_cancel_invokes_callback_and_finishes_cancelled():
    import threading

    manager = TaskManager(max_workers=1)
    started = threading.Event()
    release = threading.Event()
    cancelled = threading.Event()

    def work():
        started.set()
        release.wait(5)
        return {"ok": True}

    try:
        record = manager.submit("session-1", "cancel me", work, cancel_callback=cancelled.set)
        assert started.wait(2)
        assert manager.cancel(record.task_id) is True
        assert cancelled.is_set()
        release.set()
        record.future.result(timeout=5)
        assert manager.get(record.task_id).status == "CANCELLED"
    finally:
        manager.shutdown()
