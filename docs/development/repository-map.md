# Repository Map

```text
SOL-Lite/
├── config/                 Shipped YAML defaults (see docs/architecture/configuration.md)
├── docs/                   User, architecture, development, debugging and security docs
├── install/                Platform installation/repair/uninstall helpers
├── launcher/               Persistent Windows/macOS launchers
├── prompts/                Engineering workflow prompts
├── scripts/                Developer and platform convenience commands
├── skills/                 Built-in Agent Skills
├── src/sol_lite/
│   ├── agents/             Agent definitions, runtime, status, shell, per-agent tools
│   ├── audit/              Audit persistence
│   ├── capabilities/       Capability definitions and evidence
│   ├── config/             User settings merge (outside-repo path)
│   ├── core/               Runtime, sessions, tasks, lifecycle
│   ├── credentials/        OS keyring credential manager
│   ├── faults/             Fault logging
│   ├── integrations/       Google, Jira, SOL-Command clients
│   ├── mcp/                Optional MCP client/server (extra dependency)
│   ├── models/             Ollama/model layer and discovery
│   ├── permissions/        Policy and approvals
│   ├── platform/           Windows/macOS/Linux shell adapters
│   ├── procedures/         Checklist parser and procedure follow helpers
│   ├── remote/             Remote node manager and SSH transport
│   ├── security/           Path/command guards and secret placeholder resolution
│   ├── skills/             Skill lifecycle manager
│   ├── tools/              Registry: filesystem, terminal, repository, artifacts,
│   │                       studio, procedure, remote, searxng, sol_command, …
│   ├── ui/                 Theme tokens and composer
│   ├── voice/              STT/TTS engines and settings (data/state/voice.json)
│   ├── bootstrap.py        Config load and service wiring
│   ├── app.py              CLI entry (`sol-lite`)
│   └── terminal_ui.py      Rich presentation layer
└── tests/                  Unit, integration and battle tests
```

Persistent runtime state (not in git): workspace files under `workspace/` or `--workspace`, and `data/` for memory, audit copies, procedure state, pending skills, voice settings, and integration catalogs.
