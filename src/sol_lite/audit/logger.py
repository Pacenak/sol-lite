"""Append-only JSONL audit logger."""

import json
from datetime import UTC, datetime
from pathlib import Path


class AuditLogger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event, **data):
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            "data": data,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
