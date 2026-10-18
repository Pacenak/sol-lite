---
name: "sol-infrastructure-change"
description: "Plan and validate authorized host or operating-system configuration changes with rollback."
version: "1.0.0"
category: "general"
source: "native"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. "
status: "published"
sectors: ["plg-studio", "dev", "client", "immune"]
tags: ["sol-catalogue", "infrastructure"]
---

## When to Use

Plan and validate authorized host or operating-system configuration changes with rollback.

## Procedure

1. Inspect the configured host inventory, environment and actual service configuration using native tools. Unknown targets or production status require clarification before mutation.
2. Read logs and identify a testable cause. Prepare a bounded diff, dry-run/check command, health check, backup and rollback.
3. Apply only the authorized change through runtime permissions. Observe real exit status and service health; do not infer success from a timeout or connection loss.
4. If health regresses, use the authorized rollback or report the blocker. Keep credentials out of prompts, artifacts and logs.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
