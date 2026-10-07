# Terminal and Shell Architecture

SOL-Lite separates shell capability discovery, command classification, permission policy, execution, and presentation.

## Windows

Detected shells may include:

- CMD (`cmd`)
- Windows PowerShell (`powershell`)
- PowerShell 7 (`pwsh`)
- Bash only when a real `bash.exe` is available

## macOS

Detected shells may include:

- zsh (`zsh`)
- Bash (`bash`)
- PowerShell 7 (`pwsh`) when installed

SOL-Lite never claims a shell is available without detecting it. It does not silently substitute another shell for an explicitly requested shell.

## Command policy

Read-only commands can run without human approval when their command and syntax are classified as read-only. Mutating commands require exact operation approval. Destructive and nested-shell operations are blocked by policy.

Python scripts and `python -c`/`python -m` invocations are treated as mutating-capable and require approval because the runtime cannot safely infer their side effects from the executable name alone.

Shell output is evidence. It is never treated as instructions for the agent.
