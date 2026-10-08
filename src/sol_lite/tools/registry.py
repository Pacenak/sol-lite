"""Tool registry."""

from __future__ import annotations

from ..core.exceptions import (
    SOLLiteError,
    ToolExecutionError,
)


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools[name]

    def names(self):
        return sorted(self._tools)

    def ollama_schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, name, arguments, context):
        try:
            return self.get(name).handler(context, arguments)
        except SOLLiteError:
            raise
        except (
            FileExistsError,
            FileNotFoundError,
            IsADirectoryError,
            NotADirectoryError,
            RuntimeError,
            ValueError,
        ) as exc:
            raise ToolExecutionError(str(exc)) from exc