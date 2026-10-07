# SOL-Lite v0.2.2 Release Audit

## Scope

This audit covers the v0.2.2 pack after the Windows Ruff findings supplied during validation. It checks runtime wiring, terminal safety, skill network gating, background-task cancellation, structured runtime events, installation metadata, documentation links and generated-file hygiene.

## Findings fixed

- Removed the unused agent definition assignment in `AgentShell._make_runtime`.
- Kept the interactive shell exception boundary explicit and documented for Ruff BLE001.
- Made compound shell syntax approval-required instead of relying on incomplete nested-condition logic.
- Replaced `re.I` aliases with `re.IGNORECASE`.
- Removed the unused `os` import from runtime context.
- Removed the unused compatibility import from `runtime_context.py`.
- Corrected skill-tool import ordering.
- Corrected runtime-context test import ordering.
- Added the missing `task_manager` constructor parameter to `AgentShell`.
- Added structured runtime event publication.
- Added running-task cooperative cancellation and retained cancellation state.
- Updated foreground/background session status handling so cancellation is not reported as failure.
- Added network permission gating before external GitHub Agent Skill discovery/install.
- Corrected broken relative links in `docs/README.md`.

## Deliberate security boundaries

SOL-Lite does not attempt to prove arbitrary shell command safety with a complete parser for every supported shell. Compound syntax therefore defaults to approval. Destructive and nested-shell patterns remain blocked.

Agent Skills are inspected without execution. External GitHub access is permission-gated. Suspicious skills are quarantined. Skill content cannot grant runtime permissions.

## Validation

The Linux validation environment runs the platform-neutral suite and compile check. Windows and macOS integration tests remain platform-specific and are skipped outside their target platforms. Ruff must be run in the target environment using the installed development dependency.

## Additional validation corrections

- `StatusTracker.format_line(verbose=True)` no longer duplicates the phase label.
- `/debug` now exposes elapsed time, idle time, current tool, current command and error count in the status panel while retaining the single updating-panel model.
- The interactive shell records cancelled sessions as `CANCELLED`, not `FAILED`.
- Background tasks retain `CANCELLING` until the cooperative agent runtime returns, then settle on `CANCELLED`.
- The pack includes a standard-library-only `scripts/audit-pack.py` check and `sol-lite battle-test` runs it before compilation, pytest and Ruff.
