"""Synchronous runtime event bus."""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class Event:
    type: str
    source: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

class EventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type, callback: Callable[[Event], None]):
        self._subscribers.setdefault(event_type, []).append(callback)

    def publish(self, event: Event):
        for callback in list(self._subscribers.get(event.type, [])):
            callback(event)

    def clear(self):
        self._subscribers.clear()
