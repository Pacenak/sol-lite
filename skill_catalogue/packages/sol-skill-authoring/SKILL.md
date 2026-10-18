---
name: "sol-skill-authoring"
description: "Create and evaluate a portable SOL skill with precise routing and bounded resources."
version: "1.0.0"
category: "general"
source: "adapted"
license: "LicenseRef-SOL"
license_note: "SOL-native adaptation; upstream evidence and notices are in the shared release. anthropics/skills"
status: "published"
sectors: ["plg-studio", "dev", "client", "home", "ventures", "red-echo", "plg-film", "project-spicy", "immune", "anvil"]
tags: ["sol-catalogue", "engineering"]
---

## When to Use

Create and evaluate a portable SOL skill with precise routing and bounded resources.

## Procedure

1. Inspect existing procedures and select a concrete gap. Draft locally under .agents/skills/<name>/SKILL.md in Lite, or use Full's existing skill editor/import path; agent-authored Full skills remain drafts until reviewed.
2. Use YAML name and description. Explain when to apply the procedure; keep essential steps in the body and conditional detail in relative reference files. Do not invent tools or slash commands.
3. Define observable success, missing-dependency behavior and failure reporting. Scripts require separate inspection and normal execution permissions.
4. Test explicit invocation, one natural-language trigger, an unrelated phrase, a missing prerequisite and a failed check. Include only observed results in the review record.
5. Promote through the catalogue's reviewed build and hash verification. Never treat writing a manifest as permission to activate it globally.

## Pitfalls

Skills do not grant permissions or tool access. Report missing prerequisites and failed checks; never manufacture execution evidence.

## Verification

Map each claimed outcome to an observed result. Read [the acceptance rubric](references/acceptance.md) when validating this procedure.
