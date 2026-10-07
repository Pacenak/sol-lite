"""Concurrent session task management."""
from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TaskRecord:
    task_id: str
    session_id: str
    description: str
    status: str = "QUEUED"
    result: Any = field(default=None, repr=False)
    error: str | None = None
    future: Future | None = field(default=None, repr=False)
    cancel_callback: Callable[[], None] | None = field(default=None, repr=False)


class TaskManager:
    def __init__(self, max_workers: int = 4):
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1.")
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="sol-lite-agent")
        self._tasks: dict[str, TaskRecord] = {}
        self._lock = threading.RLock()

    def submit(
        self,
        session_id: str,
        description: str,
        fn: Callable[[], Any],
        cancel_callback: Callable[[], None] | None = None,
    ) -> TaskRecord:
        record = TaskRecord(str(uuid.uuid4()), session_id, description, cancel_callback=cancel_callback)
        with self._lock:
            self._tasks[record.task_id] = record
        future = self.executor.submit(self._run, record, fn)
        with self._lock:
            record.future = future
        return record

    def _run(self, record: TaskRecord, fn: Callable[[], Any]):
        with self._lock:
            if record.status == "CANCELLED":
                return None
            record.status = "RUNNING"
        try:
            result = fn()
            with self._lock:
                record.result = result
                if record.status in {"CANCELLING", "CANCELLED"}:
                    record.status = "CANCELLED"
                else:
                    record.status = "COMPLETED"
            return result
        except Exception as exc:
            with self._lock:
                record.error = str(exc)
                if record.status != "CANCELLED":
                    record.status = "FAILED"
            raise

    def list(self) -> list[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())

    def get(self, task_id: str) -> TaskRecord:
        with self._lock:
            return self._tasks[task_id]

    def cancel(self, task_id: str) -> bool:
        with self._lock:
            record = self._tasks[task_id]
            if record.status in {"COMPLETED", "FAILED", "CANCELLED"}:
                return False
            future = record.future
            cancel_callback = record.cancel_callback
            if future is not None and future.cancel():
                record.status = "CANCELLED"
                return True
            if cancel_callback is None:
                return False
            record.status = "CANCELLING"
        cancel_callback()
        return True

    def shutdown(self):
        self.executor.shutdown(wait=False, cancel_futures=True)
