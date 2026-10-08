"""Central capability execution boundary."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..core.exceptions import SOLLiteError, ToolExecutionError
from .evidence import EvidenceRecord


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    capability: str
    success: bool
    value: Any = None
    error: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    finished_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    evidence: EvidenceRecord | None = None


class CapabilityDispatcher:
    def __init__(self, registry):
        self.registry = registry

    def execute(self, name: str, arguments: dict[str, Any], context) -> ExecutionResult:
        capability = self.registry.get(name)
        started = datetime.now(UTC).isoformat()
        try:
            if capability.handler is None:
                raise ToolExecutionError(f"Capability '{name}' has no executable handler.")
            value = capability.handler(context, arguments)
        except SOLLiteError:
            raise
        except Exception as exc:
            raise ToolExecutionError(f"Capability '{name}' failed: {exc}") from exc
        finished = datetime.now(UTC).isoformat()
        evidence = EvidenceRecord(
            kind="capability_execution",
            source=capability.provider.value,
            target=str(arguments.get("path", arguments.get("target", ""))),
            operation=name,
            result=value,
            success=True,
            session_id=getattr(context, "session_id", None),
            capability=name,
            provenance=dict(capability.provenance),
        )
        return ExecutionResult(name, True, value, None, started, finished, evidence)
