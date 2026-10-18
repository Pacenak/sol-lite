---
name: "sol-game-production"
description: "Plan and validate a game vertical slice using the actual engine project and available build tools."
version: "1.0.0"
category: "general"
source: "native"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. "
status: "published"
sectors: ["plg-studio", "dev"]
tags: ["sol-catalogue", "game"]
---

## When to Use

Plan and validate a game vertical slice using the actual engine project and available build tools.

## Procedure

1. Identify the engine and version from the workspace; inspect gameplay code, asset references and project build instructions. Use Full's existing Studio Unreal tools only when configured.
2. Define a playable slice with input, gameplay state, persistence, UI/audio and observable acceptance checks. Label placeholder assets and missing interfaces.
3. Implement one slice and validate with the engine's real compiler/test runner. Check state transitions, deterministic replay where applicable, resource lifetime and asset import errors.
4. For multiplayer, test serialization, authority and disconnect/reconnect behavior under controlled latency; for performance, record measured frame/memory budgets and environment.
5. A source edit or mock scene is not a playable build. Report missing SDKs, unrun engine tests and device coverage explicitly.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
