# SOL-Lite Installation and First Run

SOL-Lite is installed once and then launched repeatedly from a persistent launcher. Normal startup does not recreate the venv or install dependencies.

## Windows

Install/repair:

```powershell
.\scripts\setup.bat
```

Start:

```powershell
.\launcher\windows\SOL-Lite.cmd
```

The installer also creates a Start Menu shortcut under `Programs\SOL-Lite` when run through the PowerShell installer.

Doctor:

```powershell
.\launcher\windows\SOL-Lite-Doctor.cmd
```

Repair:

```powershell
.\scripts\repair.bat
```

## macOS

Install/repair:

```bash
chmod +x scripts/*.command install/macos/*.command
./scripts/setup.command
```

Start from Applications:

```bash
open "$HOME/Applications/SOL-Lite.app"
```

The `.app` opens a Terminal session for the runtime. A repository-local launcher is also available:

```bash
./scripts/start.command
```

## First workspace

If `start` is run without `--workspace`, SOL-Lite asks the user to select a recent workspace or enter an existing directory. The selected workspace becomes the hard boundary for that session's filesystem and shell tools.

```text
sol-lite start --workspace E:\git\project
sol-lite start --workspace /Users/name/Developer/project
```

## Multiple projects

Inside the shell:

```text
/new
/workspaces
/sessions
/background <prompt>
/tasks
```

Each chat has its own session and workspace context. Background tasks use independent sessions and can run concurrently.

## Skills

```text
/skills list
/skills discover <source>
/skills import <source>
/skills update <skill>
/skills assign <skill> <agent>
/skills remove <skill>
```

External GitHub installation is network-permission gated before cloning. Suspicious skills are quarantined and imported scripts are never executed during inspection.
