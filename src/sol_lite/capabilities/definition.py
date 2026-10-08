"""Canonical capability definition shared by execution providers."""
from __future__ import annotations
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from .risk import RiskClass


class CapabilityProvider(StrEnum):
    NATIVE = "native"
    MCP = "mcp"
    SKILL = "skill"
    REMOTE = "remote"


class CapabilityLocality(StrEnum):
    HOST = "host"
    NETWORK = "network"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    identity: str
    version: str = "1"
    provider: CapabilityProvider = CapabilityProvider.NATIVE
    description: str = ""
    input_schema: Mapping[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    output_schema: Mapping[str, Any] | None = None
    permissions: tuple[str, ...] = ()
    risk: frozenset[RiskClass] = field(default_factory=lambda: frozenset({RiskClass.READ_ONLY}))
    mutability: bool = False
    platform_support: frozenset[str] = field(default_factory=frozenset)
    locality: CapabilityLocality = CapabilityLocality.HOST
    timeout_seconds: float | None = None
    cancellable: bool = False
    audit_policy: str = "standard"
    provenance: Mapping[str, Any] = field(default_factory=dict)
    handler: Callable[..., Any] | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.identity.strip():
            raise ValueError("Capability identity must not be empty.")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("Capability timeout_seconds must be positive.")

    @property
    def name(self) -> str:
        return self.identity

    @property
    def parameters(self) -> Mapping[str, Any]:
        return self.input_schema

    def as_ollama_schema(self) -> dict[str, Any]:
        return {"type": "function", "function": {"name": self.identity, "description": self.description, "parameters": dict(self.input_schema)}}
