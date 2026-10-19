# SOL-Lite Documentation

**New operator: start with [Zero-to-battle beginner runbook](getting-started/zero-to-battle-noob-runbook.md).** It explains terminal/admin access, configuration editing, agent setup, integration prerequisites and owner-only administration. Continue to [First full battle run](testing/first-full-battle-run.md) for exact fixtures, logs, checks and scoring.

**Current verification limits:** preflight passes with 56 built-in skills. The full test suite retains documented baseline failures, and source auditing reports an unchanged upstream file quarantined by Windows antivirus. See [knowledge index validation](testing/knowledge-index-consolidation.md) for exact results; a passing full suite or full source audit is not claimed.

SOL-Lite is a local-first, multi-agent engineering runtime for Windows and macOS.

## Documentation map

- [Workspace initialization templates and editing examples](../templates/workspace-init/README.md)

- [Exact knowledge retrieval and inbox consolidation](user/knowledge-index-consolidation.md)
- [Knowledge index implementation plan](superpowers/plans/2026-10-19-knowledge-index-consolidation.md)

- [Shared workspace starter pack (Stage 1)](user/workspace-starter-pack.md)

- [Personal Assistant Planner: workflow, CRUD and exports](user/personal-assistant-planner.md)
- [Personal Assistant Planner testing and adapter acceptance](testing/personal-assistant-planner.md)
- [Infrastructure automation: credential isolation, approval gates and OS command catalog](integrations/infrastructure-automation.md)
- [Infrastructure automation testing and runtime acceptance gates](testing/infrastructure-automation.md)
- [Visual agent skills: integration, routing and optional renderers](integrations/visual-agent-skills.md)
- [Visual artifacts: user prompts, formats and fallbacks](user/visual-agent-artifacts.md)
- [Visual skills test round and acceptance procedure](testing/visual-agent-skills.md)

- [Real-world Gmail and Calendar setup, with official Google references](integrations/google-real-world-setup.md)
- [Terminal SOL-Lite to Command linking and no-pending-request troubleshooting](integrations/command-real-world-linking.md)
- [Command pairing static code findings](debugging/command-pairing-static-analysis.md)

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
