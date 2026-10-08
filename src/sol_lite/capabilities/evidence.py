"""Evidence records for consequential capability execution."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    kind: str
    source: str
    target: str
    operation: str
    result: Any = None
    success: bool | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    session_id: str | None = None
    capability: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)
