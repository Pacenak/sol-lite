"""Agent registry."""

from .base import AgentDefinition


class AgentRegistry:
    def __init__(self, raw, *, data_root=None, workspace_root=None, application_config=None):
        self._agents = {}
        for agent_id, data in raw.get("agents", {}).items():
            if not data.get("enabled"):
                continue
            requires_admin = bool(
                data.get("requires_admin") or data.get("requires_studio_owner")
            )
            if requires_admin:
                try:
                    from ..security.studio_owner import admin_unlocked

                    if not admin_unlocked(
                        data_root=data_root,
                        workspace_root=workspace_root,
                        application_config=application_config,
                    ):
                        continue
                except Exception:
                    continue
            self._agents[agent_id] = AgentDefinition(
                id=agent_id,
                name=str(data["name"]),
                role=str(data["role"]),
                description=str(data["description"]).strip(),
                capabilities=tuple(data.get("capabilities", [])),
                can_delegate_to=tuple(data.get("can_delegate_to", [])),
                model_profile=str(data.get("model_profile", "engineer")),
                requires_admin=requires_admin,
                requires_studio_owner=requires_admin,
            )

    def get(self, agent_id):
        return self._agents[agent_id]

    def names(self):
        return sorted(self._agents)
