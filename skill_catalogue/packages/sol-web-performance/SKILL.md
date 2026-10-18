---
name: "sol-web-performance"
description: "Investigate React or Next.js performance using the installed stack and measured evidence."
version: "1.0.0"
category: "general"
source: "adapted"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. vercel-labs/agent-skills"
status: "published"
sectors: ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]
tags: ["sol-catalogue", "web"]
---

## When to Use

Investigate React or Next.js performance using the installed stack and measured evidence.

## Procedure

1. Confirm React/Next.js versions and the application build scripts from manifests; do not apply framework-specific changes to an unrelated engine UI.
2. Measure a representative route or bundle. Investigate request waterfalls and unnecessary payload before low-impact memoization changes.
3. Change one bottleneck, preserving rendering semantics, authentication, accessibility and cache isolation. Check the installed framework's current API.
4. Run the application's tests/build and repeat the same measurement. Report environment and before/after observations; no claimed speedup without a comparable run.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
