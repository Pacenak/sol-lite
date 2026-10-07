# SOL-Lite Runtime and Battle Testing

## Windows

### One-command developer workflow

```powershell
.\scripts\setup.bat
.\scripts\battle-test.bat
.\scripts\battle-live.bat
.\scripts\start.bat
```

`setup.bat` creates/updates the project `.venv` and never depends on PowerShell activation. `battle-test.bat` validates the harness. `battle-live.bat` validates the native Ollama agent/tool path. `start.bat` opens the interactive agent shell.


From the project root:

```powershell
.\scripts\battle-test.bat
.\scripts\battle-live.bat
.\scripts\start.bat
```

The BAT launchers always use `.venv\Scripts\python.exe`; PowerShell activation is not required.

## Direct commands

```powershell
.\.venv\Scripts\python.exe -m sol_lite doctor
.\.venv\Scripts\python.exe -m sol_lite diagnose
.\.venv\Scripts\python.exe -m sol_lite battle-test
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_engineer
.\.venv\Scripts\python.exe -m sol_lite start
```

## Agent shell

`start` launches the terminal agent shell. It provides `/agents`, `/use`, `/status`, `/tools`, `/doctor`, `/help`, and `/quit`. Ordinary input is sent to the selected agent through the native Ollama tool-call path.

## Live battle test

The live test is deliberately read-only. It requires Ollama and a configured agent model. The smoke test asks the agent to call `inventory_workspace` and verifies tool execution through the audit trail. It does not approve or perform writes.

## PowerShell execution policy

The BAT launchers do not require PowerShell script execution permission. If the `.ps1` launcher is used on a machine with restrictive policy, invoke it explicitly with:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start.ps1
```

No machine-wide execution-policy change is required.

## Agent battle coverage

The automated suite covers the harness boundaries: filesystem containment, destructive-command blocking, exact approvals, raw-tool-JSON safety, repeated-operation detection, fault-log recovery, repository controls, runtime status, CLI wiring, native-tool-call handling, and the live Ollama smoke test when `--live` is selected.

The live smoke test is intentionally read-only. It uses `sol_engineer` by default because the configured engineer profile points at `qwen3-coder:30b`. It requires Ollama to be running and that model to be installed.
