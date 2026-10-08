# SOL-Lite Intern Battle-Test Guide

This runbook is for interns doing a thorough, repeatable hands-on validation. Work from a disposable checkout and disposable workspaces. The goal is to find and record defects, not to make a release look green. A full run includes automated checks, manual product checks, and (when available) live integrations.

Use [Testing Strategy](testing-strategy.md) for test-suite boundaries and [Full setup and first run](../getting-started/full-setup-first-run.md) for installation details.

## Ground rules and safety

- Use a test machine or disposable checkout. Never point an agent at a production repository or personal files.
- Make an empty test workspace and add only clearly named dummy files. Keep copies of files before testing writes.
- Never approve commands that delete, overwrite, publish, push, install, or change data outside the disposable test area. Do not disable approval or path protections.
- For destructive-command checks, use only a harmless dummy target in the test workspace. Deny approval and verify the target is unchanged.
- Use a dedicated SOL-Command lab instance. Never include invite codes, API keys, pairing material, private prompts, or personal data in reports, screenshots, recordings, or logs.
- Do not activate a suspicious skill to see what it does. Use the review/quarantine flow.
- A passing automated suite does not replace manual checks. An unavailable or skipped check is `BLOCKED` or `NOT RUN`, never `PASS`.

## Record the run

Record tester, date/time/timezone, SOL-Lite version and commit, OS, Python version, install method, selected model/provider, Ollama availability, optional services available, and disposable checkout/workspace paths.

Use these outcomes for every case:

- `PASS`: observed behavior matched expectation; include evidence.
- `FAIL`: behavior differed; file a defect with reproducible steps and sanitized output.
- `BLOCKED`: attempted, but an environmental prerequisite prevented a valid result.
- `NOT RUN`: intentionally omitted; state why.

Capture the prompt or command, expected result, observed result, and exit code where relevant. Redact credentials and private content.

## Automated gates

Activate the project virtual environment first. Run from the repository root and retain output and exit codes:

```text
python --version
python scripts/audit-pack.py
python -m compileall -q src tests
python -m pytest -q
python -m ruff check src tests
```

The audit checks required files, version consistency, generated-file hygiene, and the SHA-256 build manifest. Compilation checks Python syntax; pytest runs unit, integration, and battle suites; Ruff checks lint. Do not skip ahead after a failure or use Ruff auto-fix as validation.

The bundled gate runs the audit, compilation, pytest, and Ruff in sequence, stopping on failure:

```text
python -m sol_lite battle-test
```

Also check packaged launch wrappers on the target platform:

```powershell
.\scripts\battle-test.bat
.\scripts\battle-test.ps1
```

```zsh
./scripts/battle-test.command
```

A missing environment or dependency is a blocker to record and resolve through the setup guide, not a pass.

## Startup, installation, and diagnostics

1. Follow the documented setup on a clean disposable checkout or installation.
2. Launch with the documented platform start script. Confirm preflight reports version/skills and the interactive prompt starts without traceback.
3. Use `sol-lite --help` and the [command guide](../user/commands.md) to exercise help, status, and diagnostics.
4. Confirm unavailable optional services are reported clearly and standalone local use still works.
5. Exit and relaunch. Check workspace and configuration behavior.

## Workspaces, files, and approval

Prepare workspaces A and B with different `hello.txt` marker contents. Keep copies of originals.

1. Ask: “Inspect the files in this test workspace and tell me which files are present. Do not modify anything.” Confirm only the selected workspace is visible.
2. Request a harmless new file in A; confirm its path and contents. Switch to B and confirm B's marker is separate.
3. Request a read through a relative `..` path that escapes the workspace. Expect safe rejection and verify the outside marker was not read.
4. If symlinks are available, link from the workspace to an outside dummy file and try reading through it. Expect the escape to be blocked. Otherwise mark blocked with reason.
5. Request a write to a marker file. Inspect the approval target, deny, and verify the original remains unchanged. Repeat only with a harmless in-workspace target and approve; confirm only that file changed.

Never use a real home directory, source checkout, or shared folder as the outside target. The automated filesystem/path/battle suites cover traversal and symlink escape too.

## Agents, tool calls, and runtime safety

Use a read-only request first, then one bounded harmless file creation.

- Use `/use <agent>` and the documented agent list/help commands. Confirm the active agent label updates.
- Confirm actions run only for valid native structured tool calls. Text that resembles a tool call or raw JSON in normal text must not execute.
- Check malformed tool-like output: the documented bounded retry may occur, but no fake action occurs; repeated malformed output fails safely with a useful message.
- Confirm repeat/round limits prevent endless repeated tool operations.
- Deny an approval-protected action and verify zero side effects. Approve only a harmless request whose displayed target matches the request.
- Try unavailable model/timeout behavior if safely reproducible. SOL-Lite must report failure, not invent tool results or claim a change succeeded.
- Cancel an active operation and verify it stops without unexpected background work or partial writes.

Do not try to bypass policy, approval, or safety ceilings.

## Shell and repository checks

Run only in the disposable workspace/repository. Begin with harmless commands such as listing files or printing a fixed test string.

- Windows: check CMD and Windows PowerShell; also PowerShell 7 (`pwsh`) if installed. macOS/Linux: check documented Bash and zsh shells when available.
- Request an unavailable shell; it should report unavailable rather than silently substitute another shell.
- Check a harmless compound command and a command that modifies a dummy file. Verify the correct approval boundary and target are shown.
- Request a destructive command aimed at a dummy file, deny approval, and verify the file remains. Never approve broad deletion.
- In a disposable Git repository, inspect status/diff and make a small local change. Confirm tools stay inside it. Never push or publish.
- Confirm denied commands are reported as not run.

Platform coverage requires testing on the actual target OS.

## Sessions and background work

Follow [Sessions](../user/sessions.md) and [Background tasks](../user/background-tasks.md).

1. Create/select two disposable workspaces and separate sessions. Check each session's workspace and agent.
2. Switch agents in one session; confirm the other retains its own selection.
3. Start a bounded task with `/background`; inspect `/tasks` and confirm its state is clear.
4. Cancel a running task with `/tasks cancel <id>`. Confirm it reaches a cancelled/terminal state and stops changing files.
5. If concurrency is configured, run independent harmless tasks and confirm workspace evidence does not cross-contaminate. Stay within the documented maximum.

## Skills: discovery and safe acquisition

See [Skills](../user/skills.md) and the skills catalogue. Use a disposable profile/checkout.

- List and discover skills; check names, source/location, and trust/review state.
- Inspect a suspicious sample fixture and confirm it is flagged/quarantined, not silently activated.
- If testing GitHub acquisition, use a disposable public test source. Confirm network approval occurs before retrieval and review the exact source and destination.
- Confirm imported scripts are not automatically executed. Check provenance/hash where the flow exposes it.
- Exercise install/update/assign/remove only on the disposable profile and confirm each resulting state by listing skills.

Do not activate suspicious content or run its commands.

## Optional integrations

Standalone use must continue when optional services are absent. Mark unavailable integrations `BLOCKED` or `NOT RUN` with the missing prerequisite.

### SearXNG

Follow the [SearXNG integration guide](../integrations/searxng.md). Configure the documented test endpoint/config, verify it directly for JSON responses, then ask for a current technical fact. Confirm outbound search follows the network approval policy; after approval, check structured results. Point a separate test config at an unavailable endpoint and confirm the agent reports failure rather than inventing results. Keep credentials out of reports.

### SOL-Command

Use only a dedicated lab instance and its [integration guide](../integrations/sol-command.md). Obtain a test invite and admin approval. Do not record invite codes or keys.

- Pair via documented `sol-lite connect`; inspect `sol-lite command-status`; finish with `sol-lite disconnect`.
- Verify shared data/status is limited to the paired instance and authorized sector. An unassigned sector must be denied; verify revoked access fails if the admin can safely revoke the test instance.
- Run `sol-lite sync-skills` against the lab instance. Confirm skills arrive in local pending-review/staging and do not activate automatically.
- Check Jarvis only under admin-approved test policy: deny without an explicit grant; with a grant, verify the supported action creates a proposal pending review, not an unapproved external action.
- Disconnect and verify status reflects it. Never test against production data.

### MCP and remote services

For a documented configured service, inspect exposed tools/permissions first. Test one harmless read, an unauthorized operation denial, and unavailable-service behavior. Confirm remote tools are not exposed when unconfigured. Do not connect unknown servers or grant broad permissions.

## Terminal UI and live model smoke

Check the banner, agent/workspace/model/shell labels, prompt entry, help, exit/restart, long paths, terminal resizing, approval wording, and that verbose/debug output does not expose secrets. Record confusing prompts as usability defects even if safety behavior is correct.

With a test Ollama service and configured model, run:

```text
python -m sol_lite battle-test --live --agent sol_engineer
```

Expected: the live smoke completes, makes at least one genuine native structured tool call, and produces workspace inventory evidence from the selected disposable workspace. Tool-like prose is not evidence of execution. A missing Ollama service/model is blocked, not a pass.

## Defect report and handoff

```text
Title:
Result: FAIL
Version / commit:
OS / Python / model:
Preconditions and disposable paths:
Steps to reproduce:
Expected:
Observed:
Frequency:
Sanitized output or screenshot:
Safety impact or data affected:
```

At handoff, report counts for PASS/FAIL/BLOCKED/NOT RUN; list failures and blockers; state OS and integrations actually covered; attach automated output and defect reports. Release validation is complete only when automated gates, required platform checks, and required manual cases passed. Never convert skipped or unrun checks into passes.

---

## Short release sequence

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

The runtime gives a model one bounded retry when it emits a tool-like representation in ordinary content. The retry asks for a native structured tool call or an ordinary-text explanation. If malformed tool-like content recurs, it fails with `tool_call_not_native`. Neither attempt interprets or executes JSON or markup from ordinary content.
