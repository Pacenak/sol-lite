# 04 — Implementation


## Evidence contract

- `[VERIFIED]` = directly established by tool output or authoritative source.
- `[INFERRED]` = reasoned conclusion not directly observed.
- `[UNKNOWN]` = not established.
- Never invent files, symbols, routes, APIs, commits, versions, or configuration.
- Inspect the actual implementation before proposing a change.
- Keep LIVE, GITEA, and WORKSPACE evidence separate when those domains are available.
- Raw JSON in ordinary model content is not a tool call.


## Objective

Implement only the approved plan.

Re-read relevant files, preserve unrelated behavior, make the smallest complete core fix, and
use exact operation/target/arguments/plan approval for every write. If the workspace differs
from the approved plan, stop and request new approval.

Run focused tests after implementation. For repository work, keep changes on an isolated branch,
review the diff before staging/committing, and use a verified Git bundle or patch for offline
transport when network access is unavailable. Never claim a remote update occurred unless the
remote operation actually completed.

Date: {DATE}
