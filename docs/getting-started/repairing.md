# Repairing an Installation

Repair is the first response to dependency or launcher problems.

## Windows

```powershell
.\install\windows\repair.ps1
.\launcher\windows\SOL-Lite-Doctor.cmd
```

## macOS

```bash
./install/macos/repair.command
```

Repair creates the venv only when missing, updates pip, installs `.[dev]`, runs Doctor, updates installation state and refreshes the macOS application bundle.
