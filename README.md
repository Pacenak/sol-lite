# SOL-Lite v0.2.5

Cross-platform, local-first multi-agent engineering runtime for **Windows and macOS**.

SOL-Lite provides isolated agent sessions, per-chat workspaces, native Ollama tool execution, controlled platform shell access, a Rich terminal UI, human approval for mutations, managed Agent Skills, concurrent background tasks, and persistent one-time installation.

## Install once, run normally

### Windows

```powershell
.\scripts\setup.bat
.\launcher\windows\SOL-Lite.cmd
```

### macOS

```bash
chmod +x scripts/*.command install/macos/*.command
./scripts/setup.command
open "$HOME/Applications/SOL-Lite.app"
```

After installation, normal startup does **not** activate a virtual environment and does **not** run `pip install`.

## Diagnostics

```text
sol-lite doctor
sol-lite diagnose
```

Platform launchers also provide Doctor. Repair is explicit.

## Core guarantees

- Every chat/session selects its own workspace.
- Workspace boundaries are enforced by normalized path containment.
- Multiple sessions and background agent tasks can coexist.
- Only native structured Ollama tool calls execute.
- Raw JSON, `<function=...>` and `<tool_call>` text are never executed.
- Tool success is based on runtime evidence, not model claims.
- The 40-round limit is a safety ceiling, not a target.
- Normal terminal mode uses one updating activity panel.
- Read-only shell operations can run when policy allows; mutations require exact approval; destructive/nested shell operations are blocked.
- Skills cannot grant permissions.
- Imported skills are inspected, hashed and provenance-recorded; suspicious skills are quarantined.

## Agents

- `sol_pa` — coordination, planning, research, scheduling and delegation.
- `sol_business` — business operations, projects, reporting and analysis.
- `sol_docs` — document workflows, metadata, indexing and extraction.
- `sol_engineer` — software engineering, debugging, testing, Git, automation and technical operations.

## Sessions and workspaces

```text
SOL-Lite
  └── Session Manager
      ├── Session A → Workspace A → Skills A
      ├── Session B → Workspace B → Skills B
      └── Session C → Workspace C → Skills C
```

First launch without `--workspace` asks the user to select a recent workspace or enter a new path.

## Terminal commands

```text
/help
/agents
/use <agent>
/new
/workspace
/workspaces
/sessions
/skills list
/skills discover <source>
/skills import <source>
/skills update <skill>
/skills assign <skill> <agent>
/skills remove <skill>
/background <prompt>
/tasks
/tasks cancel <id>
/status
/verbose
/debug
/normal
/tools
/doctor
/quit
```

## Skills

Built-in skills:

- systematic-debugging
- repository-analysis
- test-engineering
- agent-evaluation
- code-review
- git-workflow
- security-audit
- refactoring
- performance-investigation
- documentation-engineering
- handoff
- harness-audit
- shell-engineering
- skill-import

External sources require inspection and human review. GitHub skill installation checks network permission before cloning.

## Testing

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\scripts\battle-test.bat
```

macOS equivalents use `.venv/bin/python` and the `.command` scripts.

Pack integrity audit (standard library only):

```text
python scripts/audit-pack.py
```

## Design

The terminal follows the supplied Pacen/PLG colour wheel. Primary anchors are Pacen orange `#d87818`, Core cyan `#2a8fa3`, NOC cyan `#3ec6e0`, Command gold `#f5a623`, Outpost coral `#e06c75`, with neutral-dominant surfaces and semantic status colours. See `docs/design/colour-system.md` and `docs/design/colour-wheel-source.md`.

## Documentation

Start at `docs/README.md`. Documentation covers installation, first run, users, architecture, development/editing, debugging, security and Mermaid flow diagrams.

## Web search

SOL-Lite can use a private SearXNG instance through the `searxng_search` agent tool. Configure `config/searxng.yaml` or `SOL_SEARXNG_URL`; see `docs/integrations/searxng.md`.
