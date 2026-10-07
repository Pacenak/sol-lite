"""Tool types."""

from collections.abc import Callable
from dataclasses import dataclass
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

    def for_workspace(self, workspace_root, *, session_id: str | None = None, project_root=None):
        return ToolContext(
            workspace_root=workspace_root,
            permission_engine=self.permission_engine,
            audit=self.audit,
            fault_log=self.fault_log,
            platform=self.platform,
            session_id=session_id,
            project_root=project_root,
            skill_manager=self.skill_manager,
            search_config=self.search_config,
        )


@dataclass(slots=True)
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable
