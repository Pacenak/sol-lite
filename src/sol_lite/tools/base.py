"""Tool types and capability metadata."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ToolContext:
    workspace_root: Any
    permission_engine: Any
    audit: Any
    fault_log: Any
    platform: Any
    session_id: str | None = None
    project_root: Any = None
    skill_manager: Any = None
    search_config: Any = None
    authorized_resources: Any = None
    credential_manager: Any = None
    agent_id: str | None = None

    def for_workspace(self, workspace_root, *, session_id: str | None = None,
                      project_root=None, agent_id: str | None = None):
        return ToolContext(
            workspace_root, self.permission_engine, self.audit, self.fault_log,
            self.platform, session_id=session_id, project_root=project_root,
            skill_manager=self.skill_manager, search_config=self.search_config,
            authorized_resources=self.authorized_resources,
            credential_manager=self.credential_manager, agent_id=agent_id,
        )

@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable
    version: str = "1.0.0"
    permissions: tuple[str, ...] = ()
    risk: tuple[Any, ...] = ()
    mutability: bool = False
    platform_support: tuple[str, ...] = ()
    locality: str = "host"
    timeout_seconds: float | None = 120.0
    cancellable: bool = False
    audit_policy: str = "standard"
    provenance: dict[str, Any] = field(default_factory=dict)

    def as_capability(self):
        from ..capabilities.definition import (
            CapabilityDefinition,
            CapabilityLocality,
            CapabilityProvider,
        )
        from ..capabilities.risk import RiskClass
        risks = frozenset(r if isinstance(r, RiskClass) else RiskClass(r) for r in self.risk)
        return CapabilityDefinition(
            identity=self.name, version=self.version, provider=CapabilityProvider.NATIVE,
            description=self.description, input_schema=self.parameters,
            permissions=tuple(self.permissions), risk=risks, mutability=self.mutability,
            platform_support=frozenset(self.platform_support),
            locality=CapabilityLocality(self.locality), timeout_seconds=self.timeout_seconds,
            cancellable=self.cancellable, audit_policy=self.audit_policy,
            provenance=dict(self.provenance), handler=self.handler,
        )
