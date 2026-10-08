"""SOL-Lite MCP server using the official MCP Python SDK v2 low-level server."""
from __future__ import annotations

import json
from typing import Any

from ..capabilities.dispatcher import CapabilityDispatcher
from ..capabilities.registry import CapabilityRegistry
from ..capabilities.risk import RiskClass
from ..core.exceptions import SOLLiteError
from .security import AuthorizationCallback, MCPExposurePolicy

try:
    from mcp import MCPError
    from mcp.server import Server, ServerRequestContext
    from mcp.types import (
        INVALID_PARAMS,
        CallToolRequestParams,
        CallToolResult,
        ListToolsResult,
        PaginatedRequestParams,
        TextContent,
        Tool,
    )
except ImportError:  # pragma: no cover - exercised when optional dependency is absent
    MCPError = None
    Server = None


class SOLMCPServer:
    """Expose an explicit SOL-Lite capability allow-list through MCP.

    The MCP layer never becomes a permission bypass. Every capability must be
    selected by policy and, for non-read-only operations, authorized by the
    supplied callback before execution.
    """

    def __init__(
        self,
        registry: CapabilityRegistry,
        dispatcher: CapabilityDispatcher,
        context: Any,
        *,
        policy: MCPExposurePolicy | None = None,
        authorize: AuthorizationCallback | None = None,
        name: str = "SOL-Lite",
        version: str = "0.2.5",
    ) -> None:
        if Server is None:
            raise RuntimeError(
                "MCP support requires the 'mcp' package. "
                "Install the MCP optional dependency."
            )

        self.registry = registry
        self.dispatcher = dispatcher
        self.context = context
        self.policy = policy or MCPExposurePolicy()
        self.authorize = authorize
        self.server = Server(
            name,
            version=version,
            on_list_tools=self._list_tools,
            on_call_tool=self._call_tool,
        )

    def _exposed(self):
        return [
            cap for cap in self.registry.values()
            if self.policy.allows(cap)
        ]

    async def _list_tools(
        self,
        ctx: ServerRequestContext,
        params: PaginatedRequestParams | None,
    ) -> ListToolsResult:
        return ListToolsResult(
            tools=[
                Tool(
                    name=cap.identity,
                    description=cap.description,
                    input_schema=dict(cap.input_schema),
                    output_schema=(
                        dict(cap.output_schema)
                        if cap.output_schema
                        else None
                    ),
                )
                for cap in self._exposed()
            ]
        )

    async def _call_tool(
        self,
        ctx: ServerRequestContext,
        params: CallToolRequestParams,
    ) -> CallToolResult:
        try:
            cap = self.registry.get(params.name)
        except KeyError as exc:
            raise MCPError(
                INVALID_PARAMS,
                f"Unknown capability: {params.name}",
            ) from exc

        if not self.policy.allows(cap):
            raise MCPError(
                INVALID_PARAMS,
                f"Capability is not exposed: {params.name}",
            )

        arguments = dict(params.arguments or {})

        if (
            self.policy.require_authorization
            and RiskClass.READ_ONLY not in cap.risk
            and (
                self.authorize is None
                or not self.authorize(cap.identity, arguments, ctx)
            )
        ):
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="SOL-Lite authorization denied.",
                    )
                ],
                is_error=True,
            )

        try:
            result = self.dispatcher.execute(
                cap.identity,
                arguments,
                self.context,
            )
        except SOLLiteError as exc:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"Capability execution failed: {exc}",
                    )
                ],
                is_error=True,
            )

        payload = result.value
        text = (
            payload
            if isinstance(payload, str)
            else json.dumps(
                payload,
                default=str,
                ensure_ascii=False,
            )
        )

        return CallToolResult(
            content=[TextContent(type="text", text=text)],
            is_error=not result.success,
        )

    def run(self, *, transport: str = "stdio", **kwargs: Any) -> None:
        """Run the MCP server using an SDK-supported transport."""
        self.server.run(transport=transport, **kwargs)