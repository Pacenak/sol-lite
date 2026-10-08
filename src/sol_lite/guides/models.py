"""Guide and procedure domain models."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class Guide:
    identity: str
    source: str
    version: str | None = None
    platform: str | None = None
    target_type: str | None = None
    prerequisites: tuple[str, ...] = ()
    procedure: tuple[str, ...] = ()
    verification: tuple[str, ...] = ()
    rollback: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)

@dataclass(frozen=True, slots=True)
class GuideMatch:
    guide: Guide
    score: float
    reasons: tuple[str, ...] = ()
