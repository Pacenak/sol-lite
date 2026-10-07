# 05 — Validation


## Evidence contract

- `[VERIFIED]` = directly established by tool output or authoritative source.
- `[INFERRED]` = reasoned conclusion not directly observed.
- `[UNKNOWN]` = not established.
- Never invent files, symbols, routes, APIs, commits, versions, or configuration.
- Inspect the actual implementation before proposing a change.
- Keep LIVE, GITEA, and WORKSPACE evidence separate when those domains are available.
- Raw JSON in ordinary model content is not a tool call.


## Objective

Prove the fix and regression safety.

Run focused tests, affected subsystem tests, broader tests where available, lint/type checks,
the original reproduction, and at least two working-sector baselines. Do not declare success
from a build alone.

Date: {DATE}
