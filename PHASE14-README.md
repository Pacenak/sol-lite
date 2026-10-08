# SOL-Lite Phase 14 — Windows / macOS / Linux platform completion

## Scope

Phase 14 makes Linux a first-class local execution platform while retaining the
existing Windows and macOS adapters.

Supported platforms:

- Windows
- macOS
- Linux / Ubuntu

## Linux adapter

`LinuxAdapter` provides:

- bash
- sh
- zsh when installed
- fish when installed
- PowerShell (`pwsh`) when installed

The adapter does not invoke `sudo`, `su`, or other privilege escalation.
Privilege policy remains above the platform adapter.

## Platform selection

`get_platform_adapter()` now selects:

- `WindowsAdapter` for Windows
- `MacOSAdapter` for Darwin/macOS
- `LinuxAdapter` for Linux

Unknown operating systems still fail explicitly.

## Validation

Run from the repository root:

    python -m compileall -q src tests
    python -m pytest -q tests/unit/test_platform_adapters.py
    python -m pytest -q
    python -m ruff check src tests

On Linux, the bash execution test performs a real local subprocess check.

On Windows and macOS, the Linux execution test is skipped; the adapter contract
tests still execute.

## Important boundary

This phase does not add privilege escalation, remote execution, package
installation, systemd manipulation, firewall changes, or network discovery.
Those belong to the remote/infrastructure and capability policy layers.
