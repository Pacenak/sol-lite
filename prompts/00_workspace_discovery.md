# 00 — Workspace Discovery


## Evidence contract

- `[VERIFIED]` = directly established by tool output or authoritative source.
- `[INFERRED]` = reasoned conclusion not directly observed.
- `[UNKNOWN]` = not established.
- Never invent files, symbols, routes, APIs, commits, versions, or configuration.
- Inspect the actual implementation before proposing a change.
- Keep LIVE, GITEA, and WORKSPACE evidence separate when those domains are available.
- Raw JSON in ordinary model content is not a tool call.


## Objective

Build a complete read-only baseline of `{WORKSPACE}`.

## Required

1. Inventory the workspace.
2. Produce a bounded tree.
3. Identify manifests and dependencies.
4. Identify entry points.
5. Identify configuration loading.
6. Identify frontend/backend/service boundaries.
7. Identify agent/persona registries and MCP/tool registration.
8. Identify tests and test commands.
9. Separate generated artifacts from source.
10. Identify documentation/source drift.

If Anvil and working sectors exist, trace Anvil and at least two working sectors through:
`frontend → state → API/client → backend route → service → persona registry/discovery → data/rendering`.

This phase is strictly read-only.

Date: {DATE}
