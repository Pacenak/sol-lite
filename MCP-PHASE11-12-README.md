# SOL-Lite AAA — Phases 11–12: MCP Client + MCP Server

This tranche adds actual Model Context Protocol support using the official Python SDK v2.

## Implementation

- `src/sol_lite/mcp/client.py` — lifecycle-safe MCP client wrapper.
- `src/sol_lite/mcp/server.py` — low-level MCP server exposing selected SOL-Lite capabilities.
- `src/sol_lite/mcp/security.py` — explicit MCP exposure policy.
- `src/sol_lite/mcp/transport.py` — HTTP and stdio transport helpers.
- `tests/unit/test_mcp_contract.py` — policy tests that do not require the optional SDK.

## Security boundary

MCP does not grant permissions. A capability must first be exposed by the SOL-Lite MCP policy. By default only capabilities classified `READ_ONLY` are eligible. Mutating, remote, network, destructive, privileged, and credential-sensitive capabilities require an explicit policy plus an authorization callback.

Credentials are not placed in MCP schemas or model-visible results.

## Supported transports

- stdio for local MCP subprocesses.
- Streamable HTTP for deployed/network MCP servers.

SSE is deliberately not made the default because the current MCP SDK documents Streamable HTTP as the deployment transport and SSE as the older compatibility transport.

## Dependency

The MCP SDK is optional so the existing local-first runtime remains usable without MCP installed:

```text
pip install -e ".[mcp]"
```

The official SDK currently uses `MCPServer`/low-level `Server` under its v2 line and supports the 2026-07-28 protocol while negotiating with earlier revisions. SOL-Lite uses the low-level server because its canonical capability registry already owns the exact JSON Schemas.

## Important validation boundary

This ZIP is the cumulative architecture pack from the previous tranche plus Phases 11–12. It is not a claim that the GitHub `main` branch has been modified: the available GitHub integration currently permits source inspection but rejected branch creation with HTTP 403.

## Packaging note

The cumulative architecture ZIP is an architecture tranche, not a replacement for the full repository checkout. Apply the `mcp>=2.0,<3` dependency to the repository's root `pyproject.toml` under `[project.optional-dependencies]` as `mcp = ["mcp>=2.0,<3"]` before installation.
