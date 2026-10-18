---
name: "sol-security-diff"
description: "Review an authorized code diff for concrete security regressions and bounded coverage."
version: "1.0.0"
category: "general"
source: "adapted"
license: "CC-BY-SA-4.0"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. trailofbits/skills"
status: "published"
sectors: ["plg-studio", "dev", "client", "immune"]
tags: ["sol-catalogue", "security"]
---

## When to Use

Review an authorized code diff for concrete security regressions and bounded coverage.

## Procedure

1. Identify the requested revision range and inspect repository context. Focus first on changed trust boundaries, authentication, authorization and sensitive-data flows.
2. Trace changed inputs to their consumers. Inspect callers and tests before asserting exploitability; give a concrete trigger and source location for each finding.
3. Validate hypotheses using local, authorized tests. Distinguish confirmed defects, plausible concerns and unreviewed areas; do not invent a clean audit.
4. Report severity, impact, reproducible evidence and a minimal remediation. State coverage limits and avoid touching unrelated live systems.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
