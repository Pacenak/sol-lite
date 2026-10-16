"""Tool layer."""
from .artifacts import artifact_tools
from .base import ToolContext, ToolDefinition
from .filesystem import filesystem_tools
from .google_workspace import google_workspace_tools
from .hosting import hosting_tools
from .jira import jira_tools
from .notes import notes_tools
from .procedure import procedure_tools
from .registry import ToolRegistry
from .remote import remote_tools
from .repository import repository_tools
from .runtime_context import runtime_context_tools
from .search import search_tools
from .searxng import searxng_tools
from .skills import skill_tools
from .sol_command import sol_command_tools
from .studio import studio_tools
from .studio_odoo import studio_odoo_tools
from .studio_sec import studio_sec_tools
from .terminal import terminal_tools


def build_tool_registry():
    registry = ToolRegistry()
    tools = (filesystem_tools() + notes_tools() + search_tools() + terminal_tools() + repository_tools()
             + hosting_tools()
             + runtime_context_tools() + skill_tools() + searxng_tools())
    tools += sol_command_tools()
    tools += google_workspace_tools()
    tools += jira_tools()
    tools += studio_odoo_tools()
    tools += remote_tools()
    tools += procedure_tools()
    tools += studio_tools()
    tools += studio_sec_tools()
    tools += artifact_tools()
    for tool in tools:
        registry.register(tool)
    return registry


__all__ = ["ToolContext", "ToolDefinition", "ToolRegistry", "build_tool_registry"]
