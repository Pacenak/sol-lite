# SOL-Lite Documentation

**New operator: start with [Zero-to-battle beginner runbook](getting-started/zero-to-battle-noob-runbook.md).** It explains terminal/admin access, configuration editing, agent setup, integration prerequisites and owner-only administration. Continue to [First full battle run](testing/first-full-battle-run.md) for exact fixtures, logs, checks and scoring.

**Current source blockers:** preflight expects 39 built-in skills but this checkout contains 40; changed source-pack payloads also require maintainer-reviewed manifest reconciliation. See the runbook's stop conditions. These docs do not claim a working installation or passing battle.

SOL-Lite is a local-first, multi-agent engineering runtime for Windows and macOS.

## Documentation map

For full setup beyond the baseline, follow [feature configuration and all integrations](getting-started/full-feature-configuration.md), then the [first-session walkthrough](getting-started/first-session-walkthrough.md). Use the [starter prompt packs](user/starter-prompt-packs.md) for PA, Business, Docs, Engineer, integration checks and session handoffs.

New users: follow [beginner setup and first run](getting-started/full-setup-first-run.md), then the [complete beginner user guide](user/beginner-user-guide.md). The [beginner system guide](architecture/beginner-system-guide.md) explains components, files, permissions and persistence. These guides were checked by static source reading; no live installation was tested.

- [Getting started](getting-started/windows.md)
- [Full setup and first run](getting-started/full-setup-first-run.md)
- [First run and workspaces](getting-started/first-run.md)
- [User guide](user/commands.md)
- [Premium documents and diagrams](user/artifacts.md)
- [Beginner command list](user/dummies-command-list.md)
- [Studio Odoo import guide](user/dummies-studio-odoo.md)
- [Link SOL-Lite to SOL-Command (beginner)](user/dummies-command-link.md)
- [Studio change gate](user/studio-change.md)
- [Intern guide: setup, configuration, and first battle](getting-started/intern-dummies-setup-config-and-battle.md)
- [Complete skills catalogue and daily use](user/skills-full-catalog.md)
- [Configuration and environment](architecture/configuration.md)
- [CLI reference (`sol-lite …`)](user/cli-reference.md)
- [Studio change gate and procedures](user/studio-change.md)
- [Architecture](architecture/overview.md)
- [Development](development/repository-map.md)
- [MCP (optional extra)](development/mcp.md)
- [Debugging](debugging/debugging-overview.md)
- [Security](security/security-model.md)
- [Design and colour system](design/colour-system.md)
- [Testing](testing/testing-strategy.md)

All flow diagrams are Mermaid source and can be edited directly.

- [SearXNG integration](integrations/searxng.md)
- [SOL-Lite integration guide](integrations/sol-lite.md)
- [SOL-Command connection](integrations/sol-command.md)
- [Google Workspace integration](integrations/google-workspace.md)
- [Jira integration](integrations/jira.md)
- [Studio Odoo import pack](integrations/studio-odoo.md)
- [Skill catalog](architecture/skills-catalog.md)
- [Use cases](getting-started/use-cases.md)
- [Full battle test](testing/battle-test-guide.md)
- [Competence and terminal co-pilot battle](testing/competence-terminal-battle-guide.md)
