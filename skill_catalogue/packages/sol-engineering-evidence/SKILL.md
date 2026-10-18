---
name: "sol-engineering-evidence"
description: "Implement, repair or refactor software with an evidence-backed plan and validation."
version: "1.0.0"
category: "general"
source: "adapted"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. addyosmani/agent-skills, obra/superpowers"
status: "published"
sectors: ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]
tags: ["sol-catalogue", "engineering"]
---

## When to Use

Implement, repair or refactor software with an evidence-backed plan and validation.

## Procedure

1. Read supplied file paths exactly as given, then project instructions, source and relevant tests. Do not relocate a named check into a conventional tests directory without evidence. Use available read-only browsing tools to resolve missing paths. Reproduce the defect or establish a baseline before proposing a cause.
2. Record the requested outcome, scope and acceptance checks. Separate observed facts, inferred causes, assumptions and unknowns. Ask only for missing requirements that materially change implementation.
3. Plan small changes with the files and checks that prove them. Create a regression test for a behavioral defect when useful; observe its failure for the expected reason. Do not force test-first work for cosmetic changes.
4. Make the smallest justified edit using the runtime's native tools. Preserve unrelated edits and public contracts. Check dependency/API versions in the project before using them.
5. Run relevant checks, inspect exit codes and output, then review the diff against the acceptance criteria. A successful write is not a passing test; a later failed check invalidates earlier completion evidence.
6. Report changed behavior, exact checks and outcomes, remaining uncertainty and blockers. If validation failed, repair within scope or report incomplete. Never replace tool execution with a plausible narrative.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
