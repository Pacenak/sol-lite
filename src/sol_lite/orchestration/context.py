"""Bounded task context independent of a model provider."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TaskContext:
    objective: str
    session_id: str | None = None
    workspace_root: str | None = None
    project_root: str | None = None
    constraints: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    recent_events: deque[dict[str, Any]] = field(default_factory=lambda: deque(maxlen=128))

    def add_event(self, event: dict[str, Any]) -> None:
        self.recent_events.append(dict(event))

    def add_evidence(self, evidence: dict[str, Any]) -> None:
        self.evidence.append(dict(evidence))

    def add_validation(self, result: dict[str, Any]) -> None:
        self.validation_results.append(dict(result))

    def snapshot(self) -> dict[str, Any]:
        return {"objective": self.objective, "session_id": self.session_id, "workspace_root": self.workspace_root, "project_root": self.project_root, "constraints": list(self.constraints), "decisions": list(self.decisions), "evidence": list(self.evidence), "changed_files": list(self.changed_files), "validation_results": list(self.validation_results), "unresolved": list(self.unresolved), "recent_events": list(self.recent_events)}


class ContextManager:
    def __init__(self, context: TaskContext):
        self.context = context

    def add_constraint(self, value: str) -> None:
        if value and value not in self.context.constraints:
            self.context.constraints.append(value)

    def add_decision(self, value: str) -> None:
        if value and value not in self.context.decisions:
            self.context.decisions.append(value)

    def add_changed_file(self, path: str) -> None:
        if path and path not in self.context.changed_files:
            self.context.changed_files.append(path)

    def add_unresolved(self, value: str) -> None:
        if value and value not in self.context.unresolved:
            self.context.unresolved.append(value)

    def compact_events(self, keep: int = 32) -> None:
        if keep < 1:
            raise ValueError("keep must be at least 1.")
        while len(self.context.recent_events) > keep:
            self.context.recent_events.popleft()

    def snapshot(self) -> dict[str, Any]:
        return self.context.snapshot()
