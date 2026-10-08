"""MCP exposure and authorization policy."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..capabilities.risk import RiskClass


@dataclass(frozen=True, slots=True)
class MCPExposurePolicy:
    """Explicit allow-list for capabilities exposed over MCP."""

    allowed_capabilities: frozenset[str] = field(
        default_factory=frozenset
    )

    denied_capabilities: frozenset[str] = field(
        default_factory=frozenset
    )

    allowed_risks: frozenset[RiskClass] = field(
        default_factory=lambda: frozenset(
            {RiskClass.READ_ONLY}
        )
    )

    require_authorization: bool = True

    def allows(
        self,
        capability: Any,
        *,
        transport: str = "stdio",
        authorized: bool = False,
    ) -> bool:
        name = capability.identity

        # Explicit deny always wins over allow.
        if name in self.denied_capabilities:
            return False

        # When an allow-list is present, anything not explicitly listed
        # is denied.
        if (
            self.allowed_capabilities
            and name not in self.allowed_capabilities
        ):
            return False

        risks = set(capability.risk)

        # No declared risk is not a safe declaration.
        if not risks:
            return False

        # Every declared risk must be explicitly allowed.
        if not risks.issubset(self.allowed_risks):
            return False

        # A capability is read-only only when READ_ONLY is its sole risk.
        read_only = risks == {RiskClass.READ_ONLY}

        # Non-stdio transports cross the MCP process boundary and must
        # therefore have an explicit authorization decision even for
        # read-only capabilities.
        if transport != "stdio" and not authorized:
            return False

        # Mutating / privileged / remote / network / destructive /
        # credential-sensitive capabilities require explicit authorization.
        if (
            self.require_authorization
            and not read_only
            and not authorized
        ):
            return False

        return True


AuthorizationCallback = Callable[
    [str, dict[str, Any], Any],
    bool,
]