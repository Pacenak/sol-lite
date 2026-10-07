"""Runtime health result."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class HealthResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def success(cls, warnings=None):
        return cls(True, warnings=warnings or [])

    @classmethod
    def failure(cls, errors, warnings=None):
        return cls(False, errors=list(errors), warnings=warnings or [])
