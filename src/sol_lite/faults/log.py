"""Atomic JSON fault log."""

import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path


class FaultLog:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._save({"version": 1, "created_at": self._now(), "faults": []})

    @staticmethod
    def _now():
        return datetime.now(UTC).isoformat()

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return {"version": 1, "created_at": self._now(), "faults": []}
        if not isinstance(data, dict) or not isinstance(data.get("faults"), list):
            return {"version": 1, "created_at": self._now(), "faults": []}
        return data

    def _save(self, data):
        fd, temp_name = tempfile.mkstemp(prefix=self.path.name + ".", suffix=".tmp",
                                         dir=str(self.path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)

    def log(self, **fault):
        data = self._load()
        record = {"timestamp": self._now(), **fault}
        data["faults"].append(record)
        self._save(data)
        return record

    def get_all(self):
        return list(self._load()["faults"])
