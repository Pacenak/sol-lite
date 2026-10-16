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

Studio manuals are loaded with `procedure_load`. Fenced command blocks are not executed. File creates, edits, and quarantines go through `studio_create`, `studio_edit`, and `studio_quarantine`. Copies of files that are not in Git are written under `data/state/backups/`. The staff page is [Studio change gate](../user/studio-change.md).

## Skill commands

- `/skills list`
- `/skills discover <source>`
- `/skills import <source>`
- `/skills update <skill>`
- `/skills assign <skill> <agent>`
- `/skills remove <skill>`
