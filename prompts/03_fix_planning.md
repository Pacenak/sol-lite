# 03 — Fix Planning


## Evidence contract

- `[VERIFIED]` = directly established by tool output or authoritative source.
- `[INFERRED]` = reasoned conclusion not directly observed.
- `[UNKNOWN]` = not established.
- Never invent files, symbols, routes, APIs, commits, versions, or configuration.
- Inspect the actual implementation before proposing a change.
- Keep LIVE, GITEA, and WORKSPACE evidence separate when those domains are available.
- Raw JSON in ordinary model content is not a tool call.


## Objective

Create an exact implementation plan without modifying files.

For every change specify exact path, symbol/function/hook/route, existing behavior, required
change, causal rationale, risk, regression tests, validation commands and rollback strategy.

The plan must be deterministic enough for exact approval hashing. No writes.

Date: {DATE}
