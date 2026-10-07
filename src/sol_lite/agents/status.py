"""Low-noise runtime status tracker."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

MAX_TOOL_ROUNDS = 40


@dataclass(slots=True)
class AgentActivity:
    status: str = "IDLE"
    phase: str = "INTERACTIVE"
    activity: str = "Waiting for input"
    started_at: float | None = None
    last_activity_at: float | None = None
    operation_started_at: float | None = None
    round_number: int = 0
    max_rounds: int = MAX_TOOL_ROUNDS
    tool_calls: int = 0
    tools_completed: int = 0
    files_read: int = 0
    files_written: int = 0
    commands_executed: int = 0
    errors: int = 0
    current_tool: str | None = None
    current_command: str | None = None
    cancelled: bool = False


class StatusTracker:
    def __init__(self, heartbeat_interval=1.0, slow_threshold=45.0, stall_threshold=90.0):
        self.heartbeat_interval = heartbeat_interval
        self.slow_threshold = slow_threshold
        self.stall_threshold = stall_threshold
        self._a = AgentActivity()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._callback = None

    def start(self, callback=None):
        self._callback = callback
        self._stop.clear()
        self._thread = threading.Thread(target=self._heartbeat, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=max(self.heartbeat_interval * 2, 1))

    def begin(self, phase, activity):
        now = time.monotonic()
        with self._lock:
            self._a = AgentActivity(status="WORKING", phase=phase, activity=activity,
                                    started_at=now, last_activity_at=now)

    def finish(self, status="IDLE", activity="Waiting for input"):
        with self._lock:
            self._a.status = status
            self._a.activity = activity
            self._a.current_tool = None
            self._a.current_command = None
            self._a.operation_started_at = None

    def touch(self, activity=None):
        with self._lock:
            self._a.last_activity_at = time.monotonic()
            if activity:
                self._a.activity = activity

    def set_round(self, number):
        with self._lock:
            self._a.round_number = number
            self._a.last_activity_at = time.monotonic()

    def tool_start(self, name):
        with self._lock:
            self._a.tool_calls += 1
            self._a.current_tool = name
            self._a.operation_started_at = time.monotonic()
            self._a.activity = f"Running {name}"

    def tool_complete(self, name):
        with self._lock:
            self._a.tools_completed += 1
            self._a.current_tool = None
            self._a.operation_started_at = None
            self._a.last_activity_at = time.monotonic()
            self._a.activity = f"Completed {name}"

    def error(self):
        with self._lock:
            self._a.errors += 1
            self._a.last_activity_at = time.monotonic()

    def cancel(self):
        with self._lock:
            self._a.cancelled = True
            self._a.status = "CANCELLED"

    def snapshot(self):
        with self._lock:
            return AgentActivity(**{name: getattr(self._a, name) for name in AgentActivity.__dataclass_fields__})

    def state(self):
        a = self.snapshot()
        if a.status != "WORKING" or a.last_activity_at is None:
            return a.status
        age = time.monotonic() - a.last_activity_at
        if age >= self.stall_threshold:
            return "STALLED"
        if age >= self.slow_threshold:
            return "SLOW"
        return "WORKING"

    def format_line(self, verbose=False):
        a = self.snapshot()
        now = time.monotonic()
        elapsed = 0 if a.started_at is None else now - a.started_at
        idle = 0 if a.last_activity_at is None else now - a.last_activity_at
        status = self.state()
        parts = [status, a.phase, a.activity, f"{elapsed:.0f}s"]
        if verbose:
            parts.append(f"round {a.round_number}/{a.max_rounds}")
            parts.append(f"idle {idle:.0f}s")
            parts.append(f"tools {a.tools_completed}/{a.tool_calls}")
        return " · ".join(parts)

    def _heartbeat(self):
        while not self._stop.wait(self.heartbeat_interval):
            if self._callback:
                self._callback(self.format_line())
