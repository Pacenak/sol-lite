---
name: "sol-mcp-adapter"
description: "Build an MCP adapter against actual schemas while preserving SOL permissions and native hosting."
version: "1.0.0"
category: "general"
source: "adapted"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. anthropics/skills"
status: "published"
sectors: ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]
tags: ["sol-catalogue", "integration"]
---

## When to Use

Build an MCP adapter against actual schemas while preserving SOL permissions and native hosting.

## Procedure

1. Inspect SOL's existing MCP manager, transport and permission policy before designing an adapter; do not create a second host.
2. Read the target server's official schema and record transport, version, authentication and tool names. Keep absent tools unavailable; repository listings do not establish a connection.
3. Implement input/output validation, credential references, timeouts and explicit read/write classification. Avoid retrying a timed-out mutation without checking its actual state.
4. Test a real configured read, an invalid argument and a denied mutation; keep live write tests scoped to a disposable authorized resource. No credentials or external service are enabled by installing this skill.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
