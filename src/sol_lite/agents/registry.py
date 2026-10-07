"""Agent registry."""

from .base import AgentDefinition


class AgentRegistry:
    def __init__(self, raw):
        self._agents = {}
        for agent_id, data in raw.get("agents", {}).items():
            if data.get("enabled"):
                self._agents[agent_id] = AgentDefinition(
                    id=agent_id, name=str(data["name"]), role=str(data["role"]),
                    description=str(data["description"]).strip(),
                    capabilities=tuple(data.get("capabilities", [])),
                    can_delegate_to=tuple(data.get("can_delegate_to", [])),
                    model_profile=str(data.get("model_profile", "engineer")),
                )

    def get(self, agent_id):
        return self._agents[agent_id]

    def names(self):
        return sorted(self._agents)
