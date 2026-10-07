"""Agent definition."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    id: str
    name: str
    role: str
    description: str
    capabilities: tuple[str, ...] = ()
    can_delegate_to: tuple[str, ...] = ()
    model_profile: str = "engineer"
