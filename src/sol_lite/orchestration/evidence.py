"""Evidence ledger used by orchestration and reporting."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceEntry:
    kind: str
    source: str
    operation: str
    target: str
    result: Any = None
    success: bool | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class EvidenceLedger:
    def __init__(self) -> None:
        self._entries: list[EvidenceEntry] = []

    def record(self, *, kind: str, source: str, operation: str, target: str, result: Any = None, success: bool | None = None) -> EvidenceEntry:
        entry = EvidenceEntry(kind, source, operation, target, result, success)
        self._entries.append(entry)
        return entry

    def all(self) -> list[EvidenceEntry]:
        return list(self._entries)

    def successful(self, operation: str | None = None) -> list[EvidenceEntry]:
        return [entry for entry in self._entries if entry.success is True and (operation is None or entry.operation == operation)]

    def has_successful_operation(self, operation: str) -> bool:
        return bool(self.successful(operation))
