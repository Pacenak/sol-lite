"""MCP transport configuration helpers."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MCPHTTPConfig:
    url: str
    mode: str = "auto"

    def validate(self) -> None:
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("MCP HTTP URL must use http:// or https://")


def stdio_target(command: str, args: list[str] | None = None, env: dict[str, str] | None = None) -> Any:
    from mcp.client.stdio import StdioServerParameters
    return StdioServerParameters(command=command, args=args or [], env=env)
