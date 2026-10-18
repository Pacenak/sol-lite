---
name: "sol-container-hardening"
description: "Review container configuration and propose verified hardening for an authorized environment."
version: "1.0.0"
category: "general"
source: "adapted"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. mukul975/Anthropic-Cybersecurity-Skills"
status: "published"
sectors: ["plg-studio", "dev", "client", "immune"]
tags: ["sol-catalogue", "security"]
---

## When to Use

Review container configuration and propose verified hardening for an authorized environment.

## Procedure

1. Inventory the actual Dockerfile, runtime configuration, image source and deployment environment. Do not assume a Docker daemon or remote target is available.
2. Review user privileges, capabilities, writable paths, mounted sockets, secrets and image provenance against the service's functional requirements.
3. Propose a configuration diff and rollback. Validate with locally configured Docker tooling; never pull a scanner, restart production or push an image merely because a reference procedure mentions it.
4. Report observed findings and test output. Mark daemon/host controls unverified unless inspected on an authorized host.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
