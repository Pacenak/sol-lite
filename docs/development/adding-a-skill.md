# Adding a Skill

Built-in skills live under `skills/<skill-id>/SKILL.md`.

Use YAML frontmatter with `name` and `description`. Keep the body procedural and bounded. Never place permission-granting instructions in a skill; permissions belong to configuration and the runtime.

## Optional intent registration

```yaml
---
name: topology-preview
description: Create editable topology diagrams and local previews.
metadata:
  trigger-phrases: "topology preview|draw topology"
---

Read the supplied topology, write editable source and validate the output.
```

The phrase field must be a pipe-separated string. Use specific task phrases rather than generic words such as `create` or `file`. Discovery parses it automatically; no new Python dispatch branch is needed. Workspace `.agents/skills/<name>/SKILL.md` works through the same path. Skill IDs should match folder names.

Test actual prompt injection with `SkillManager.prompt_context`, including a positive phrase, uppercase/repeated whitespace, a substring that must not match, an explicit `$skill-name` invocation and a mixed-capability request. Do not use a fixed total skill count as the only catalogue assertion. Keep old manifests without metadata compatible.

For optional renderers, describe concrete commands and prerequisites, provide an offline fallback, and distinguish source creation, structural validation, rendering and visual inspection. Never imply a service exists because a manifest mentions it. See [visual skills integration](../integrations/visual-agent-skills.md).
