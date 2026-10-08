"""Model provider contracts used by the SOL-Lite model gateway."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    """Capabilities advertised by a model endpoint."""

    tool_calling: bool = False
    structured_output: bool = False
    vision: bool = False
    coding: bool = False
    reasoning: bool = False
    context_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class ModelEndpoint:
    """Provider endpoint metadata without credentials."""

    provider: str
    endpoint: str
    locality: str = "host"
    trusted: bool = False
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)


class ModelProvider(ABC):
    """Minimal provider interface retained for existing providers."""

    @abstractmethod
    def chat(self, model, messages, tools, temperature, timeout):
        raise NotImplementedError

    def capabilities(self, model: str | None = None) -> ModelCapabilities:
        """Return provider/model capabilities when known."""
        return ModelCapabilities()

    def endpoint(self) -> ModelEndpoint:
        raise NotImplementedError
