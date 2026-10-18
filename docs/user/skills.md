# Agent Skills

The [shared skill catalogue](shared-skill-catalogue.md) provides pinned SOL-Lite /
SOL-Full engineering and optional domain packs, dependency reports and rollback.

To create a skill yourself or ask an agent to create one, follow the
[authoring, injection and acceptance workflow](../development/adding-a-skill.md).
Start with a workspace `.agents/skills/<skill-id>/SKILL.md`, inspect it with
`/skills show <skill-id>`, and invoke `$<skill-id>` in your task. Import a reviewed
copy when you need it across workspaces.

The [Personal Assistant Planner](personal-assistant-planner.md) provides document-grounded scheduling, protected lifestyle boundaries, CRUD rules and Markdown/JSON/iCalendar templates. Invoke `$personal-assistant-planner` or use a phrase such as “plan my week.” See its [testing runbook](../testing/personal-assistant-planner.md) for verified scope and adapter requirements.

Built-in skills are reviewed and versioned with the runtime. External skills follow a discovery/inspection/security/provenance/human-review flow.

Commands:

```text
/skills list
/skills discover <source>
/skills import <source>
/skills update <skill>
/skills assign <skill> <agent>
/skills remove <skill>
```

Supported sources include local directories, `SKILL.md`, ZIP archives and GitHub repositories.

Imported scripts are never executed during inspection. Suspicious content is quarantined. Skills cannot grant permissions.


For descriptions, routing and daily-use prompt recipes, see [Complete Skills Catalogue and Daily Use](skills-full-catalog.md). Use `/skills list` to inspect the current catalogue rather than a fixed historical count.

Visual artifact skills are built in: `architecture-diagrams`, `slide-deck-generator` and `image-markup-ui`. Describe the job normally or include an explicit `$architecture-diagrams`, `$slide-deck-generator` or `$image-markup-ui` mention in your prompt. These mentions select instructions; they are not terminal commands. See [Visual artifacts](visual-agent-artifacts.md) for examples, dependencies and export limitations.
