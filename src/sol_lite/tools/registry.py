"""Native tool registry backed by canonical capability definitions."""
from __future__ import annotations

from ..capabilities.risk import RiskClass
from ..core.exceptions import SOLLiteError, ToolExecutionError
from .base import ToolDefinition


_READ = {
    "inventory_workspace",
    "list_project_structure",
    "find_workspace_files",
    "read_workspace_file",
    "read_workspace_files",
    "get_workspace_file_metadata",
    "search_codebase",
    "analyze_architecture_drift",
    "runtime_get_context",
    "repository_status",
    "repository_diff",
    "repository_log",
    "repository_branches",
    "repository_remotes",
    "searxng_search",
    "skill_discover",
}


_MUTATING = {
    "write_workspace_file",
    "execute_terminal_command",
    "repository_create_branch",
    "repository_checkout",
    "repository_stage",
    "repository_commit",
    "repository_create_bundle",
    "repository_import_bundle",
    "repository_create_patch",
    "repository_apply_patch",
    "repository_merge_import",
    "repository_set_remote",
    "repository_fetch",
    "repository_push",
    "repository_clone_remote",
    "repository_clone_local",
    "skill_install",
}


_REPOSITORY_REMOTE = {
    "repository_set_remote",
    "repository_fetch",
    "repository_push",
    "repository_clone_remote",
}


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        if tool.name in self._tools:
            raise ValueError(
                f"Duplicate tool: {tool.name}"
            )

        if not tool.permissions:
            if tool.name in _READ:
                tool.permissions = (
                    "filesystem.read",
                )

            elif tool.name == "write_workspace_file":
                tool.permissions = (
                    "filesystem.write",
                )

            elif (
                tool.name in _REPOSITORY_REMOTE
            ):
                tool.permissions = (
                    "repository.remote",
                )

            elif (
                tool.name in _MUTATING
                and tool.name.startswith(
                    "repository_"
                )
            ):
                tool.permissions = (
                    "repository.write",
                )

            elif (
                tool.name
                == "execute_terminal_command"
            ):
                tool.permissions = (
                    "terminal.write",
                )

            elif tool.name == "skill_discover":
                tool.permissions = (
                    "skills.inspect",
                )

            elif tool.name == "skill_install":
                tool.permissions = (
                    "skills.install",
                )

            else:
                tool.permissions = ()

        if not tool.risk:
            if tool.name in _READ:
                tool.risk = (
                    RiskClass.READ_ONLY,
                )

            elif (
                tool.name
                in _REPOSITORY_REMOTE
            ):
                tool.risk = (
                    RiskClass.MUTATING,
                    RiskClass.REMOTE,
                    RiskClass.NETWORK,
                )

            else:
                tool.risk = (
                    RiskClass.MUTATING,
                )

        tool.mutability = (
            tool.name in _MUTATING
        )

        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools[name]

    def names(self):
        return sorted(self._tools)

    def values(self):
        return tuple(
            self._tools.values()
        )

    def capabilities(self):
        return {
            name: tool.as_capability()
            for name, tool in self._tools.items()
        }

    def ollama_schemas(self):
        return [
            tool.as_capability().as_ollama_schema()
            for tool in self._tools.values()
        ]

    def execute(
        self,
        name,
        arguments,
        context,
    ):
        try:
            tool = self.get(name)

            permission_engine = getattr(
                context,
                "permission_engine",
                None,
            )

            if (
                permission_engine is not None
                and hasattr(
                    permission_engine,
                    "execution_context",
                )
            ):
                with permission_engine.execution_context(
                    session_id=getattr(
                        context,
                        "session_id",
                        None,
                    ),
                    agent_id=getattr(
                        context,
                        "agent_id",
                        None,
                    ),
                    capability=name,
                    risk=tool.risk,
                ):
                    return tool.handler(
                        context,
                        arguments,
                    )

            return tool.handler(
                context,
                arguments,
            )

        except SOLLiteError:
            raise

        except (
            FileExistsError,
            FileNotFoundError,
            IsADirectoryError,
            NotADirectoryError,
            RuntimeError,
            ValueError,
            PermissionError,
        ) as exc:
            raise ToolExecutionError(
                str(exc)
            ) from exc