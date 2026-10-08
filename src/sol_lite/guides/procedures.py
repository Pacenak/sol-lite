"""Guide procedure planning without executing instructions."""
from __future__ import annotations

from dataclasses import dataclass

from .models import Guide


@dataclass(frozen=True, slots=True)
class ProcedurePlan:
    guide_identity: str
    source: str
    steps: tuple[str,...]
    verification: tuple[str,...]
    rollback: tuple[str,...]
    warnings: tuple[str,...]

def build_plan(guide: Guide) -> ProcedurePlan:
    if not guide.procedure:
        raise ValueError(f"Guide '{guide.identity}' contains no procedure steps")
    return ProcedurePlan(guide.identity,guide.source,guide.procedure,guide.verification,guide.rollback,guide.warnings)
