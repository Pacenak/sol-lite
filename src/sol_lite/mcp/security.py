"""MCP exposure and authorization policy."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..capabilities.risk import RiskClass


@dataclass(frozen=True, slots=True)
class MCPExposurePolicy:
    """Explicit allow-list for capabilities exposed over MCP."""

    allowed_capabilities: frozenset[str] = field(default_factory=frozenset)
    denied_capabilities: frozenset[str] = field(default_factory=frozenset)
    allowed_risks: frozenset[RiskClass] = field(default_factory=lambda: frozenset({RiskClass.READ_ONLY}))
    require_authorization: bool = True

    def allows(self, capability: Any) -> bool:
        name = capability.identity
        if name in self.denied_capabilities:
            return False
        if self.allowed_capabilities and name not in self.allowed_capabilities:
            return False
        return set(capability.risk).issubset(self.allowed_risks)


AuthorizationCallback = Callable[[str, dict[str, Any], Any], bool]
