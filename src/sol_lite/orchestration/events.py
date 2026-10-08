"""Event/evidence integration helpers."""
from __future__ import annotations
from typing import Any

def publish_transaction_event(event_bus, event_type: str, transaction_id: str, **data: Any) -> None:
    if event_bus is not None:
        from ..core.event_bus import Event
        event_bus.publish(Event(event_type, "transaction_engine", {"transaction_id": transaction_id, **data}))
