# Approvals

Mutating operations can require human approval. The approval record binds the operation, target, arguments and plan hash.

`y` approves that exact operation once. `s` approves the same permission scope for the rest of the session (file writes inside the agent role, or terminal writes that are not destructive). Approving one scope does not approve a different scope.

Destructive commands stay blocked (`mkfs`, `format`, `reboot`, `shutdown`, `rm`). Nested shells (`cmd /c`, `powershell -Command`, `bash -c`) stay blocked. Choose `cmd`, `powershell`, `pwsh`, `bash`, or `zsh` with the terminal tool's `shell` argument instead.

`sudo`, `chmod`, and `chown` are not a free pass. They need `y` or a session `s`. Disk wipe and reboot stay blocked even after that yes.

Every agent can create, overwrite, and edit files under its role paths (`docs/`, `plans/`, `notes/`, `src/`, and the other roots for that agent) without a click. A path outside the role still needs `y` for that exact file. Session `s` still covers other approval scopes for the rest of the chat (for example terminal writes that are not destructive). Destructive commands stay blocked.
