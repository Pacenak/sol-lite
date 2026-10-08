"""Model Context Protocol integration for SOL-Lite."""

from .client import MCPClient, MCPClientConfig, MCPToolInfo
from .server import MCPExposurePolicy, SOLMCPServer

__all__ = ["MCPClient", "MCPClientConfig", "MCPToolInfo", "MCPExposurePolicy", "SOLMCPServer"]
