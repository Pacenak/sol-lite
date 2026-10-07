# SOL-Lite Full Battle-Test Guide

This is the release validation sequence for Windows and macOS. Do not mark a release PASS from a partial run.

## A. Static pack audit

```text
python scripts/audit-pack.py
```

Expected: `SOL-Lite pack audit: PASS`.

## B. Python compilation

```text
python -m compileall -q src tests
```

Expected: exit code 0.

## C. Unit/integration/battle tests

```text
python -m pytest -q
```

Platform-specific skips are acceptable only when the skip reason is explicit and the platform-specific test is run on its target OS.

## D. Ruff

```text
python -m ruff check src tests
```

Expected: zero findings. Do not use `--fix` as the release validation step; review and commit fixes first.

## E. SearXNG integration

1. Configure `config/searxng.yaml` or `SOL_SEARXNG_URL`.
2. Verify SearXNG directly with `curl` and `format=json`.
3. Run SOL-Lite.
4. Ask an agent to search for a current technical fact.
5. Confirm the first external search triggers the expected network approval under the default policy.
6. Approve it.
7. Confirm structured search results are returned.
8. Test an unavailable SearXNG endpoint and confirm the agent reports failure instead of inventing results.

## F. Skill acquisition

Test local skill discovery, GitHub source inspection, suspicious-skill quarantine, exact install approval, and source hashing. Network access must be gated before GitHub cloning.

## G. Agent runtime

Test: native tool calls, tool-like text rejection, raw JSON rejection, repeat guard, approval denial, approval grant, cancellation, task cancellation, stalled status, event emission, and safety ceiling.

## H. Shell

On Windows test CMD, Windows PowerShell, and PowerShell 7 when installed. On macOS test zsh and Bash. Confirm unavailable shells are not silently substituted. Test compound commands and mutation commands for approval.

## I. Workspace/session

Create two workspaces. Start separate sessions. Verify each session retains the correct workspace and that background tasks do not cross-contaminate contexts.

## J. Full live smoke test

With Ollama running:

```text
python -m sol_lite battle-test --live --agent sol_engineer
```

The live test must produce at least one native structured tool call and workspace inventory evidence.

## Windows wrapper

```powershell
.\scripts\battle-test.bat
```

## macOS wrapper

```zsh
./scripts/battle-test.command
```

## Release rule

A release is PASS only when the static audit, compile, test, Ruff, and required platform checks pass. A missing dependency or unavailable external service must be reported as such, not silently converted into PASS.
