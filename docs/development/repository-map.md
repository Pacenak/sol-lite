# Repository Map

```text
SOL-Lite/
├── config/                 Runtime configuration
├── docs/                   User, architecture, development, debugging and security docs
├── install/                Platform installation/repair/uninstall helpers
├── launcher/               Persistent Windows/macOS launchers
├── prompts/                Engineering workflow prompts
├── scripts/                Developer and platform convenience commands
├── skills/                 Built-in Agent Skills
├── src/sol_lite/
│   ├── agents/             Agent definitions, runtime, status and shell
│   ├── audit/              Audit persistence
│   ├── core/               Runtime, sessions and tasks
│   ├── faults/             Fault logging
│   ├── models/             Ollama/model layer
│   ├── permissions/        Policy and approvals
│   ├── platform/           Windows/macOS shell adapters
│   ├── security/           Path and command guards
│   ├── skills/             Skill lifecycle manager
│   ├── tools/              Filesystem, terminal, repository, context and skill tools
│   ├── ui/                 Theme tokens
│   └── terminal_ui.py      Rich presentation layer
└── tests/                  Unit, integration and battle tests
```
