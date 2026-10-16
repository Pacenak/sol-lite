# MCP (Model Context Protocol)

SOL-Lite includes an **optional** MCP client and a low-level MCP server implementation. The current `pyproject.toml` does not declare an `mcp` extra. The core local-first runtime works without MCP installed.

## Install

There is no supported beginner `pip install -e ".[mcp]"` path in this manifest. An implementer must supply an MCP SDK version compatible with the interfaces imported by `client.py` and `server.py`, wire the transport and authorization policy, and verify that integration. The source references SDK v2 interfaces; this documentation does not establish compatibility with an arbitrary installed package version. The application CLI has no MCP server-start subcommand.

Implementation lives under `src/sol_lite/mcp/` (`client.py`, `server.py`, `security.py`, `transport.py`). Policy tests are in `tests/unit/test_mcp_contract.py`.

## Security boundary

MCP does **not** grant permissions by itself. A capability must be exposed by SOL-Lite MCP policy first. By default only capabilities classified read-only are eligible. Mutating, remote, network, destructive, privileged, and credential-sensitive capabilities need explicit policy plus an authorization callback. Credentials are not placed in MCP schemas or model-visible results.

This matches the product rule that skills and MCP exposure cannot widen the permission engine.

## Transports

- **stdio** — local MCP subprocesses
- **Streamable HTTP** — deployed/network MCP servers

SSE is not the default transport; the SDK treats Streamable HTTP as the primary deployment path.

## Documentation gap note

Battle tests mention MCP alongside remote services; there is no separate operator guide for starting the SOL-Lite MCP server from launchers yet. Treat MCP as a developer integration surface until a user-facing runbook is added. The architecture pack notes remain in the repository root `MCP-PHASE11-12-README.md` for implementers.

## Related

- [Tool system](../architecture/tool-system.md)
- [Security model](../security/security-model.md)
