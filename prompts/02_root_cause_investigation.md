# 02 — Root Cause Investigation


## Evidence contract

- `[VERIFIED]` = directly established by tool output or authoritative source.
- `[INFERRED]` = reasoned conclusion not directly observed.
- `[UNKNOWN]` = not established.
- Never invent files, symbols, routes, APIs, commits, versions, or configuration.
- Inspect the actual implementation before proposing a change.
- Keep LIVE, GITEA, and WORKSPACE evidence separate when those domains are available.
- Raw JSON in ordinary model content is not a tool call.


## Objective

Prove the causal defect.

Inspect each candidate layer, compare it with working sectors, identify the first divergence,
and demonstrate why that divergence can produce the observed behavior. Check registration,
loading, filtering, state, API, backend, rendering and lifecycle.

Do not declare a root cause without causal evidence. If causality cannot be proven, mark it
`[UNKNOWN]`.

This phase is read-only.

Date: {DATE}
