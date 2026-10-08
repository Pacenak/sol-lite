"""Canonical capability registry."""
from __future__ import annotations
from .definition import CapabilityDefinition


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityDefinition] = {}

    def register(self, capability: CapabilityDefinition) -> None:
        if capability.identity in self._capabilities:
            raise ValueError(f"Duplicate capability: {capability.identity}")
        self._capabilities[capability.identity] = capability

    def get(self, name: str) -> CapabilityDefinition:
        try:
            return self._capabilities[name]
        except KeyError as exc:
            raise KeyError(f"Unknown capability: {name}") from exc

    def names(self) -> list[str]:
        return sorted(self._capabilities)

    def values(self) -> list[CapabilityDefinition]:
        return list(self._capabilities.values())

    def ollama_schemas(self) -> list[dict]:
        return [capability.as_ollama_schema() for capability in self._capabilities.values()]
