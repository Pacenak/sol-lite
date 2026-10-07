---
name: open-code-review
description: Review code for correctness, regressions, security, maintainability, performance, tests, and operational risk.
---

# Deep Code Review

## Review order
1. Correctness and behavior
2. Security and permissions
3. Regression risk
4. Error handling and cancellation
5. Concurrency/state
6. Performance
7. Tests and observability
8. Maintainability

Report concrete findings with file/line evidence when available.


## SOL-Lite boundary
This skill provides reasoning guidance only. It does not grant filesystem, terminal, repository, network, skill-install, or application permissions. Runtime policy and explicit approvals remain authoritative.
