"""Tool layer."""
from .base import ToolContext, ToolDefinition
from .filesystem import filesystem_tools
from .registry import ToolRegistry
from .repository import repository_tools
from .runtime_context import runtime_context_tools
from .search import search_tools
from .searxng import searxng_tools
from .skills import skill_tools
from .terminal import terminal_tools


def build_tool_registry():
    registry = ToolRegistry()
    tools = (filesystem_tools() + search_tools() + terminal_tools() + repository_tools()
             + runtime_context_tools() + skill_tools() + searxng_tools())
    for tool in tools:
        registry.register(tool)
    return registry


__all__ = ["ToolContext", "ToolDefinition", "ToolRegistry", "build_tool_registry"]
