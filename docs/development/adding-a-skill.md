# Adding a Skill

## User and agent authoring workflow

1. Define the outcome, required inputs, supported tools and observable success
   checks. Inspect the current repository before naming commands or APIs.
2. Create `.agents/skills/<skill-id>/SKILL.md` in the approved workspace.
   Users can write this file directly; agents use the workspace write/edit tools
   under the existing permission policy. Use the manifest example below.
3. Write steps to inspect inputs, state assumptions, perform the task and validate
   results. Specify how to report missing prerequisites, uncertainty and failed
   checks. Never describe an unexecuted command as successful.
4. Add reference files or scripts beside the manifest when needed. Keep their
   paths relative to the skill folder and document dependencies. Only the selected
   `SKILL.md` body is injected automatically; supporting files must be read using
   workspace tools if accessible, and scripts require normal execution permissions.
5. Run `/skills list` and `/skills show <skill-id>` in that workspace. Request
   `$<skill-id>` explicitly and verify the actual task behavior. Also check an
   unrelated request to ensure trigger phrases do not overmatch.
6. For reuse across workspaces, use `/skills discover <source>`, then
   `/skills import <source>`, review the displayed warnings and approve installation.
   Import assigns to the active agent; `/skills assign <skill-id> <agent-id>` adds
   another agent. Sources may be a local folder, SKILL.md, ZIP or GitHub clone URL.

Workspace discovery loads local instructions without the external import review
flow. Inspect workspace skills before using an unfamiliar repository. Skill text
cannot authorize access, enable tools or bypass approvals. External imports with
warnings (including executable scripts) are quarantined by the interactive import
and agent installation tools; inspect them rather than expecting automatic activation.

## Injection and acceptance checks

The runtime lists available skill descriptions and injects selected manifest
bodies through `SkillManager.prompt_context`. Explicit `$skill-id` mentions and
specific `metadata.trigger-phrases` select the full body; generic relevance
matches have a four-skill limit. Installed skills retain their agent assignments.
ZIP/Git discoveries are retained as pending content until installation; pending
content is not active. Installation checks that the candidate still matches its
inspected hash.

Before calling a new skill ready, verify: explicit selection, automatic phrase
selection, no selection for a misleading substring, correct agent assignment,
missing-dependency reporting, a successful real task and a deliberately failing
validation. Prompt inclusion alone does not prove reliable execution.

For engineering acceptance, use a small repository task with a known defect:
require an evidence-based diagnosis, a bounded plan, a real edit, relevant tests
and a diff review. Repeat with an ambiguous requirement and a failed test. The
agent must label the ambiguity and report failure without claiming completion.
Automated runtime tests cover some false-completion patterns; they cannot prove
that every natural-language claim or model response is correct.

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
