# Agent Skills

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


For all 33 built-in skills, descriptions, routing and daily-use prompt recipes, see [Complete Skills Catalogue and Daily Use](skills-full-catalog.md).
