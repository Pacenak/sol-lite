"""SOL-Lite MCP client wrapper around the official MCP Python SDK v2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from mcp import Client
    from mcp.client.stdio import StdioServerParameters
except ImportError:  # pragma: no cover
    Client = None
    StdioServerParameters = None


@dataclass(frozen=True, slots=True)
class MCPClientConfig:
    target: str | Any
    mode: str = "auto"


@dataclass(frozen=True, slots=True)
class MCPToolInfo:
    name: str
    description: str | None
    input_schema: dict[str, Any]
    output_schema: dict[str, Any] | None


class MCPClient:
    """Lifecycle-safe MCP client.

    A URL uses Streamable HTTP. ``StdioServerParameters`` can be supplied for
    a local subprocess. The official SDK performs protocol-era negotiation.
    """

    def __init__(self, config: MCPClientConfig) -> None:
        if Client is None:
            raise RuntimeError("MCP support requires the 'mcp' package. Install the MCP optional dependency.")
        self.config = config
        self._client = Client(config.target, mode=config.mode)

    async def __aenter__(self):
        await self._client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self._client.__aexit__(exc_type, exc, tb)

    @property
    def protocol_version(self) -> str | None:
        return self._client.protocol_version

    @property
    def server_info(self):
        return self._client.server_info

    async def list_tools(self) -> list[MCPToolInfo]:
        result = await self._client.list_tools()
        return [
            MCPToolInfo(
                name=tool.name,
                description=tool.description,
                input_schema=dict(tool.input_schema),
                output_schema=dict(tool.output_schema) if tool.output_schema else None,
            )
            for tool in result.tools
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None):
        return await self._client.call_tool(name, arguments or {})
