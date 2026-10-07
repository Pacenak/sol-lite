# Terminal, Sessions, and Skills Quick Reference

## Display modes

- Normal: one live-updating status panel, readable conversation panels, Markdown responses.
- `/verbose`: expanded round/tool/status details.
- `/debug`: runtime-oriented diagnostics.
- `/normal`: return to normal display.

## Session commands

- `/new` — new agent chat and workspace selection.
- `/workspace` — current workspace.
- `/workspaces` — recent/named workspaces.
- `/sessions` — active session records.
- `/background <prompt>` — concurrent background task.
- `/tasks` — background task status.

## Shell commands

Agents can request `cmd`, `powershell`, `pwsh`, `bash`, or `zsh` only when the runtime detects that shell. Shell selection is explicit.

## Skill commands

- `/skills list`
- `/skills discover <source>`
- `/skills import <source>`
- `/skills update <skill>`
- `/skills assign <skill> <agent>`
- `/skills remove <skill>`
