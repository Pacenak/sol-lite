# Changelog

## 0.2.5

- Corrected Rich Panel API usage so Rich 15 renders all SOL-Lite panels without `title_style` errors.
- Added regression coverage for user, agent, failure, and approval panels.
- Corrected installer and macOS bundle version metadata to 0.2.5.
- Corrected the runtime bridge warning version.
- Implemented `/workspace [path|number|new]` to match the documented command contract.
- Added workspace and version consistency regression tests.


## 0.2.4

- Fixed Rich 15 compatibility: `Panel` title styling now uses styled `Text` titles instead of the removed `title_style` argument.
- Fixed `/skills` so built-in and workspace skills are listed from the active agent/workspace context.
- Added `/skills show <skill>` for detailed skill inspection.
- Added `/skill` as a safe alias for `/skills`.
- Added complete beginner command and daily skill-use documentation.


## 0.2.3

### Skills and research
- Expanded the built-in Agent Skill library with debugging, architecture, diagramming, Mermaid, code review, prompt engineering, product, planning, humanizer, UI/UX, career-operations, web-research, and source-verification skills.
- Added an auditable registry of the requested external skill repositories and references. External material remains inspect/install gated rather than silently executable.
- Added full use-case and battle-test documentation for the expanded skill system.

### SearXNG
- Added the `searxng_search` native structured tool for private SearXNG instances.
- Added configurable URL, timeout, result limits, categories, language, safe-search, and engine selection.
- Added environment overrides and network permission/approval enforcement.
- Added SearXNG configuration, troubleshooting, security-boundary, and validation documentation.


## 0.2.2

### Installation and lifecycle
- Added idempotent cross-platform installation and repair helpers.
- Added persistent installation state under `data/state/install.json`.
- Added Windows and macOS persistent launchers so normal restarts do not require venv activation or dependency setup.
- Added macOS `.app` launcher packaging and Windows command launchers.
- Added explicit repair and uninstall flows that preserve source/configuration/workspaces.

### Runtime and multitasking
- Fixed the interactive shell constructor wiring for task management.
- Added background task result/error retention and cooperative running-task cancellation.
- Added `/tasks cancel <id>` with explicit `CANCELLING` state handling.
- Corrected foreground/background session status so cancellation is not reported as failure.
- Added structured agent/model/tool/approval lifecycle event publication.
- Fixed duplicate phase text in verbose status output.
- Added actual debug status details without reverting to heartbeat-line spam.
- Preserved per-session workspace isolation.

### Security
- External GitHub Agent Skill discovery/install now checks network permission before network access.
- Network approvals are consumable and can be followed by the separate exact skill-install approval.
- Compound shell syntax is approval-required instead of relying on incomplete nested-condition handling.
- Native structured tool calls remain the only executable model tool-call path.

### Diagnostics
- Expanded `sol-lite doctor` with environment, dependency and installation-state diagnostics.
- Rich version checks use `importlib.metadata.version()` and do not rely on the removed `rich.__version__` attribute.

### Documentation
- Added complete installation, first-run, user, architecture, development, debugging, security and editable Mermaid flow documentation.
- Added the supplied Pacen/PLG colour-wheel source reference to the pack.
- Added the v0.2.2 release audit and dependency/launcher troubleshooting notes.
- Corrected broken documentation-relative links.

## 0.2.1

- Pacen/PLG terminal colour-system integration and terminal UI refinement.

## 0.2.0

- Sessions and per-chat workspaces.
- Background task manager.
- Native structured Ollama tool-call enforcement.
- Windows/macOS shell capability detection and command classification.
- Agent Skills discovery, validation, provenance and quarantine.
