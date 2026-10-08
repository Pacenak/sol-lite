"""Native tool registry backed by canonical capability definitions."""
from __future__ import annotations
from ..capabilities.risk import RiskClass
from ..core.exceptions import SOLLiteError, ToolExecutionError
from .base import ToolDefinition

_READ = {"inventory_workspace","list_project_structure","find_workspace_files","read_workspace_file",
         "read_workspace_files","get_workspace_file_metadata","search_codebase","analyze_architecture_drift",
         "runtime_get_context","repository_status","repository_diff","repository_log","repository_branches",
         "repository_remotes","searxng_search","skill_discover"}
_MUTATING = {"write_workspace_file","execute_terminal_command","repository_create_branch","repository_checkout",
             "repository_stage","repository_commit","repository_create_bundle","repository_import_bundle",
             "repository_create_patch","repository_apply_patch","repository_merge_import","repository_set_remote",
             "repository_fetch","repository_push","repository_clone_remote","repository_clone_local",
             "skill_install"}

class ToolRegistry:
    def __init__(self): self._tools: dict[str, ToolDefinition] = {}
    def register(self, tool: ToolDefinition):
        if tool.name in self._tools: raise ValueError(f"Duplicate tool: {tool.name}")
        if not tool.permissions:
            tool.permissions = ("filesystem.read",) if tool.name in _READ else ("filesystem.write",) if tool.name == "write_workspace_file" else ("repository.write",) if tool.name in _MUTATING and tool.name.startswith("repository_") else ("terminal.write",) if tool.name == "execute_terminal_command" else ("skills.inspect",) if tool.name == "skill_discover" else ("skills.install",) if tool.name == "skill_install" else ()
        if not tool.risk:
            tool.risk = (RiskClass.READ_ONLY,) if tool.name in _READ else (RiskClass.MUTATING,)
        tool.mutability = tool.name in _MUTATING
        self._tools[tool.name] = tool
    def get(self,name): return self._tools[name]
    def names(self): return sorted(self._tools)
    def values(self): return tuple(self._tools.values())
    def capabilities(self): return {n:t.as_capability() for n,t in self._tools.items()}
    def ollama_schemas(self): return [t.as_capability().as_ollama_schema() for t in self._tools.values()]
    def execute(self,name,arguments,context):
        try:
            tool = self.get(name)
            permission_engine = getattr(context, "permission_engine", None)
            if permission_engine is not None and hasattr(permission_engine, "execution_context"):
                with permission_engine.execution_context(session_id=getattr(context, "session_id", None), agent_id=getattr(context, "agent_id", None), capability=name, risk=tool.risk):
                    return tool.handler(context, arguments)
            return tool.handler(context, arguments)
        except SOLLiteError: raise
        except (FileExistsError,FileNotFoundError,IsADirectoryError,NotADirectoryError,RuntimeError,ValueError,PermissionError) as exc:
            raise ToolExecutionError(str(exc)) from exc
