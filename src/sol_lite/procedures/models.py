"""Parsed studio checklist rows."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ProcedureStep:
    step_id: str
    action: str
    validate: str
    classification: str
    section: str = ""
    action_command: str = ""
    validate_command: str = ""
    required_status: str = ""
    outcome: str = "pending"
    evidence: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.classification == "blocked":
            self.outcome = "blocked"
        elif self.classification == "unverifiable":
            self.outcome = "unverifiable"


@dataclass(slots=True)
class ProcedureDocument:
    source: str
    steps: tuple[ProcedureStep, ...]
    unparsed_sections: tuple[str, ...] = ()

    @property
    def complete(self) -> bool:
        if self.unparsed_sections or not self.steps:
            return False
        return all(step.outcome in {"verified", "human_gate"} for step in self.steps)
