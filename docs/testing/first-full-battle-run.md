# First full battle run: beginner operator sequence

Follow [zero-to-battle setup](../getting-started/zero-to-battle-noob-runbook.md) first. This chapter describes actions for the operator; none were run by the documentation author. Use a normal terminal and test data. A full battle is automated gates **plus** live agent/tool checks **plus** each configured feature's observed results. One `PASS` line is not proof of all integrations.

## 1. Define results and prerequisites

Record tester, local date/time/timezone, OS, Python version, application version, Git commit, model tags, test checkout, workspace paths and enabled integrations. Do not record tokens, invite codes, private mailbox contents or owner unlock details.

For every case use:

- `PASS`: expected behavior was observed, with evidence.
- `FAIL`: product/release behavior differed from its implemented/documented contract.
- `BLOCKED`: a prerequisite prevented a valid check.
- `NOT RUN`: deliberately omitted; state why.

An unsupported developer feature should be identified as unsupported, not tested as though it were available. A model/service missing on the machine is a blocker, not a pass. A failed release gate cannot be labelled a passed battle because chat still opens.

Prerequisites: complete source checkout, intended Python environment, reviewed configuration, Ollama reachable, configured text models downloaded, and appropriate disposable accounts/hosts for any integration you want to test. Do not run as Windows Administrator. OS setup belongs before this battle.

## 2. Create fixtures and logs outside the source checkout

From normal PowerShell in the checkout, run once for a fresh battle. If the folder already contains another run, choose a new folder name before creating files; these fixture commands write files deliberately.

```powershell
$battleRoot = Join-Path $env:USERPROFILE 'SOL-Lite-Battle-First'
$battleA = Join-Path $battleRoot 'A'
$battleB = Join-Path $battleRoot 'B'
$battleEvidence = Join-Path $battleRoot 'evidence'
New-Item -ItemType Directory -Force -Path $battleA, $battleB, $battleEvidence
New-Item -ItemType Directory -Force -Path (Join-Path $battleA 'docs')
Set-Content -LiteralPath (Join-Path $battleA 'hello.txt') -Value 'BATTLE-A-UNCHANGED'
Set-Content -LiteralPath (Join-Path $battleB 'hello.txt') -Value 'BATTLE-B-UNCHANGED'
Set-Content -LiteralPath (Join-Path $battleA 'sample.py') -Value "def add(a, b):`n    return a - b"
Set-Content -LiteralPath (Join-Path $battleA 'README.md') -Value '# Battle Demo: a deliberately broken addition example.'
Set-Content -LiteralPath (Join-Path $battleRoot 'outside-marker.txt') -Value 'OUTSIDE-FIXTURE-ONLY'
Get-Content -LiteralPath (Join-Path $battleA 'hello.txt')
Get-Content -LiteralPath (Join-Path $battleA 'sample.py')
```

A and B are agent workspaces. Evidence is for the human operator. Never give the entire battle root as workspace for the containment case: its outside marker must stay outside A.

Create `A/docs/lab-manual.md` in your editor with this harmless dry-run fixture:

```markdown
# Lab marker procedure
1. Read hello.txt and identify this workspace.
2. Propose creating scratch.txt containing BATTLE-SCRATCH.
3. Read scratch.txt only after the operator separately authorizes creation.
Stop before every change. Do not install software, contact services or delete files.
```

Record basic environment evidence:

```powershell
git rev-parse HEAD
git status --short
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m sol_lite version
ollama list
```

Keep logs outside the source because pack audit includes eligible payload files. Do not start a broad terminal transcript during account connection/token entry; save only sanitised relevant outputs.

## 3. Understand the pack audit stop condition

Read `scripts/audit-pack.py`: it compares the manifest's file set and SHA-256 hashes to eligible files under the checkout. It runs **before** preflight in the bundled battle. Local documentation/configuration changes or new eligible files can invalidate a packaged manifest.

Current source also has 40 skill folders while preflight requires 39. These are independent gates:

```text
AUDIT ERROR: Manifest missing files: ...
AUDIT ERROR: Manifest hash mismatch: ...
PREFLIGHT FAIL: expected 39 built-in skills, found 40
```

Do not regenerate a supplied release manifest to erase evidence of an unexpected changed release. Preserve the error and ask the maintainer to identify the intended source payload.

For a deliberate, reviewed **development build**, a maintainer regenerates the manifest after intended files are final:

```powershell
.\.venv\Scripts\python.exe scripts\build-manifest.py
```

That changes `BUILD_MANIFEST.json`; it is a packaging operation, not a test or security proof. No manifest was regenerated while writing these docs. The skill-count contract still requires a source fix/reconciliation. Obtain that corrected build before claiming an end-to-end battle pass.

If the audit blocks the bundled command, separately executed checks below may produce useful diagnostic evidence, but they do not override its failure. Record exactly which gates ran.

## 4. Run each automated gate once with evidence

From the checkout, with the fixture variables still defined, run each block separately. After failure stop the normal sequence and capture the cause. A senior/maintainer may authorize independent diagnostic checks, labelled as such.

### Pack audit

```powershell
.\.venv\Scripts\python.exe scripts\audit-pack.py 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '01-pack-audit.txt')
$auditExit = $LASTEXITCODE
"audit exit=$auditExit"
```

Expected exit `0` and `SOL-Lite pack audit: PASS`.

### Preflight

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '02-preflight.txt')
$preflightExit = $LASTEXITCODE
"preflight exit=$preflightExit"
```

Expected exit `0` with the version/Rich/skill-count pass line matching the intended source. The present 39/40 mismatch is a fail until reconciled.

### Compilation

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '03-compilation.txt')
$compileExit = $LASTEXITCODE
"compile exit=$compileExit"
```

Quiet output with exit `0` means syntax compilation passed. This executes Python compilation and creates bytecode caches; it is not a static-only review.

### Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q -ra 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '04-pytest.txt')
$pytestExit = $LASTEXITCODE
"pytest exit=$pytestExit"
```

Expected exit `0` and no failed cases. `-ra` lists skip reasons. Platform/missing-renderer skips are not evidence of those features working. Tests may use mocks, temporary files and subprocesses; they do not establish live provider health.

### Lint

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '05-ruff.txt')
$ruffExit = $LASTEXITCODE
"ruff exit=$ruffExit"
```

Expected exit `0` and no findings. Do not use `--fix` as a validation step.

The convenience command `python -m sol_lite battle-test` through the `.venv` interpreter runs those five checks in order (its pytest uses `-q`) and stops at the first nonzero result. You may use it instead of individual checks once the gates are understood; there is no need to repeat all passing automated checks without a change or unresolved issue.

## 5. Native live smoke for each agent

The source's `--live` command repeats the entire automated gate, then runs one agent. It checks for at least one native tool call and new `workspace.inventory` audit evidence. It is not a direct live-only switch.

Point its tool context at the disposable A folder, then run each command separately, stopping on a failure:

```powershell
$env:SOL_WORKSPACE_ROOT = $battleA
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_pa 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '06-live-pa.txt')
$livePaExit = $LASTEXITCODE
"PA live exit=$livePaExit"
```

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_business 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '07-live-business.txt')
$liveBusinessExit = $LASTEXITCODE
"Business live exit=$liveBusinessExit"
```

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_docs 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '08-live-docs.txt')
$liveDocsExit = $LASTEXITCODE
"Docs live exit=$liveDocsExit"
```

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_engineer 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '09-live-engineer.txt')
$liveEngineerExit = $LASTEXITCODE
"Engineer live exit=$liveEngineerExit"
```

For each expect exit `0`, `LIVE AGENT PASS: AGENT_ID; ...` and `SOL-Lite battle test: PASS`. Confirm A's marker and `sample.py` remain unchanged. An automated gate failure prevents the live step; record **live NOT RUN due to prior gate**, rather than blaming Ollama for a request never made.

## 6. Interactive agent evidence

Start PA in A:

```powershell
.\.venv\Scripts\python.exe -m sol_lite start --agent sol_pa --workspace "$battleA"
```

Run `/workspace`, `/agents`, `/skills list` and `/tools` separately. The workspace must be A. Each specialist below needs actual input-file reads, not recollection or guesses:

- **PA:** plan this battle in the reply only, using the fixture facts. No file changes/network.
- **Business:** read `hello.txt` and `sample.py`; explain the current result of `add(2,1)` in the reply only.
- **Docs:** read the files and draft a short clear report in the reply only. Artifact creation is a separate case.
- **Engineer:** read `sample.py`, identify subtraction and propose `return a + b`; do not edit or run it yet.

Use `/use sol_business`, `/use sol_docs`, `/use sol_engineer` before the matching prompt. Expected `add(2,1)` by source reading is `1`, not a claimed executed result. All input files should remain unchanged.

## 7. Permissions and workspace containment

Use Engineer in A. Perform each case separately and save sanitised prompt/result evidence:

1. **Role-path write:** request creation of only `docs/role-marker.txt` containing `ROLE-MARKER`, then read it back. Under the default enabled write scope, this role-path file may not need a popup. That is documented behavior, not an approval bypass defect.
2. **Out-of-role approval denial:** request `approval-marker.txt` at A's root, which is outside Engineer's role prefixes. Deny its exact write prompt. Confirm the file is absent. If an earlier broad session grant was issued, restart first.
3. **Exact approval:** repeat that harmless request and approve only the intended file. Read back `APPROVAL-MARKER`.
4. **Traversal:** ask the file-reading tool to read `../outside-marker.txt`. Expected safe rejection, not the marker content. This tests file containment, not the permissions of arbitrary subprocesses.
5. **Workspace switch:** `/workspace` with the full B path, read `hello.txt`, then switch back to A. Expect B and A's distinct marker contents. Use full paths pasted from the fixture variables in PowerShell; do not type the variable names as chat paths.
6. **Tool-shaped prose:** ask for an explanation of tool-call JSON as text without executing anything. No fake invocation should create a file. Automated raw-JSON/tool-like-content suites are the stronger deterministic coverage.
7. **Blocked commands:** do not run destructive actions manually. The automated command/security suites cover them. If a senior requests a manual denial case, target only a disposable marker and never approve it.

The workspace boundary does not constitute an OS sandbox for all possible shell programs. Keep test prompts and approved commands strictly scoped. Do not test with real outside private files.

## 8. Terminal and procedure checks

Request the harmless `echo SOL-BATTLE` using installed `cmd` or PowerShell on Windows. The result should name the selected shell, give exit status `0` and stdout with the marker. A missing `pwsh`, Bash or zsh is a missing optional shell, not a reason to silently substitute one.

Use `/follow docs/lab-manual.md`, then ask Engineer to load/inspect the same manual without acknowledging/advancing or running steps. The report should show candidates and human gates. `scratch.txt` must still be absent.

Older competence documentation contains `/shell operator` and `/shell session` as proposed contracts. **The current slash-command dispatcher implements neither.** Do not document these as available privilege switches or follow those cases to bypass command guards. The implemented controls are configured scopes, exact/session approvals where offered, role-path rules and fixed command restrictions.

For a deliberately approved harmless fixture change, request only creation of `scratch.txt` with the marker, then read it back. If denied, verify absence; if accepted, verify exact content. Do not equate manual loading with step execution.

## 9. Workspace memory, handoff and background tasks

Ask PA to call `workspace_notes_write` with a short factual note describing A and its subtraction bug, then `workspace_notes_read`. The default saved location is `data/memory/<workspace_id>/notes.md`, outside A. That write is intentional application state, not a violation of the project-output path.

Quit/relaunch on A and ask for the saved note. It should be retrievable. Do not expect all chat history to survive: sessions are held in memory and only six turn pairs are kept in recent context.

Start one read-only background inspection:

```text
/background Read hello.txt and sample.py and report the intentional subtraction bug. Do not write files, execute commands or contact services.
/tasks
```

Verify a terminal state and result. For cancellation, use the real task ID and observe cancelled/completed state rather than assuming it stops instantly. A very fast task may complete before cancellation; record that as not exercised, not a cancellation pass.

Create a final workspace handoff using the [starter handoff prompt](../user/starter-prompt-packs.md#review-and-handoff-pack) only after reviewing actual results.

## 10. All built-in skills

The historical intern chapter lists 39 ordinary skills, including `agent-skill-curation`, but lacks a dedicated prompt for that entry. This tree additionally contains owner-gated `studio-admin-toolbelt`, bringing the total to 40. Enumerate the actual files rather than trusting an old count:

```powershell
Get-ChildItem .\skills -Directory | ForEach-Object { if (Test-Path (Join-Path $_.FullName 'SKILL.md')) { $_.Name } }
```

For each ordinary skill: choose an agent where `/skills list` shows it, run `/skills show ID`, read its guidance, then use its [intern skill prompt](../getting-started/intern-dummies-setup-config-and-battle.md#9-first-battle-of-every-built-in-skill) against A. Replace the old fixture text `battle-marker-intern` with `BATTLE-A-UNCHANGED`. Skill availability and correct guidance are separate from successful execution of a feature requiring extra services.

For `agent-skill-curation`, use:

```text
Read the agent-skill-curation guidance and inspect the skill catalogue available to this agent. Explain how you would choose one relevant skill for reviewing sample.py and how you would identify unsupported or duplicate guidance. Do not import, update, remove or execute any skill or modify files.
```

For `studio-admin-toolbelt`, mark blocked unless the authorised owner has completed the separate admin setup. Under that owner session, show the guidance and check owner status without scanning hosts. A skill that describes security tools does not prove those tools load or run.

For missing/inactive skill guidance, record the actual result; do not assign every skill to every role to force coverage. For web/artifact/Odoo skills, complete prerequisite checks or mark them blocked. Keep one outcome/evidence record per actual catalogue entry.

The static inventory for this checkout is below. Use one score-sheet entry for each line; a future reviewed release can change the inventory and its matching preflight contract.

```text
agent-evaluation
agent-skill-curation
agile-sprint-planning
architecture-design
book-to-skill
career-operations
code-review
copilot-patterns
debugging-error-recovery
debugging-methodology
diagram-design
document-layout
documentation-engineering
git-workflow
handoff
harness-audit
humanizer
infrastructure-discovery
mermaid-diagrams
open-code-review
performance-investigation
planning-and-estimation
presentation-design
product-discovery
product-management
prompt-engineering
readable-plans
refactoring
repository-analysis
security-audit
shell-engineering
skill-import
spreadsheet-reporting
studio-admin-toolbelt
studio-odoo-import
systematic-debugging
test-engineering
ui-ux-design
web-research-searxng
web-source-verification
```

## 11. Strict artifact renderer acceptance

After authoring packages, LibreOffice and Mermaid CLI are installed, use a fresh output folder outside the source:

```powershell
$env:SOL_REQUIRE_ARTIFACT_RENDERERS = '1'
$env:SOL_ARTIFACT_ACCEPTANCE_OUTPUT = Join-Path $battleRoot 'artifact-acceptance'
.\.venv\Scripts\python.exe -m pytest -q -ra tests/integration/test_artifact_renderers.py 2>&1 | Tee-Object -FilePath (Join-Path $battleEvidence '10-artifact-acceptance.txt')
$artifactExit = $LASTEXITCODE
"artifact acceptance exit=$artifactExit"
```

With the strict flag, missing renderer dependencies fail instead of silently skipping. The source creates Office/diagram fixtures, asserts outputs/previews and returns `rendered_unreviewed`. It explicitly records visual review as not performed. Open the generated files and every preview yourself and record legibility, clipping, pagination and spreadsheet values. On macOS the strict test also asserts Microsoft Office applications are absent; use the intended acceptance environment rather than deleting installed applications to satisfy it.

Remove only the temporary environment entries when finished:

```powershell
Remove-Item Env:SOL_REQUIRE_ARTIFACT_RENDERERS -ErrorAction SilentlyContinue
Remove-Item Env:SOL_ARTIFACT_ACCEPTANCE_OUTPUT -ErrorAction SilentlyContinue
```

## 12. Integration battle cases

Configure each through [full integration setup](../getting-started/full-feature-configuration.md), then use its [starter prompt](../user/starter-prompt-packs.md#integration-check-pack). Scope the first battle to disposable accounts/data. Save sanitised evidence outside the checkout.

- **SearXNG:** direct request returns JSON; an approved agent search returns actual URLs; an unreachable lab endpoint is reported as a failure, not fabricated results. Restore the correct configuration afterwards.
- **Google:** consent/saved status, then one approved narrow Gmail read and one calendar interval read. Do not count saved authorization as API success. For write coverage, use a dedicated test mailbox and test event only after reviewing full details; record the created identifiers and arrange human/provider-side cleanup.
- **Jira:** live status, a granted-project read, and rejection of an ungranted project without contacting it. Writes require a test project and exact approval; ask its administrator about cleanup. Do not use production issues.
- **Command:** administrator-approved Lite pairing, live assigned-sector status, permitted memory/metadata read, pending skill download with no automatic activation. Verify revoked/unassigned access only with the lab administrator. Jarvis write coverage requires an explicit grant and yields a pending ticket, not applied changes. Disconnect/revoke the lab instance when done.
- **Git:** local status/diff and a deliberate small fixture change in a separately initialised disposable repository. Do not push/publish as an ordinary first-battle case. Hosting PR checks require an explicitly provided disposable GitHub-compatible repository.
- **SSH/PowerShell remoting:** list configured lab nodes, approve one harmless OS-identification read, deny a write and verify no changed target. An unconfigured node must be rejected. Do not change firewall/service settings during the battle.
- **Studio procedures/backups:** dry load does not run a step; existing-file creation reports existence; approved untracked edit has a verified backup; production edits are refused. Use disposable lab data and [Studio tests/runbook](battle-test-guide.md).
- **Odoo:** unbound status, supplied-template bind, schema/inventory, rejected wrong-header fixture with no output, approved valid dummy CSV under the test workspace, no Odoo API/filing. Source values/catalogue codes must be valid; do not invent tax data to make a file pass.
- **Voice:** actual microphone recognition and speaker playback, plus missing-provider behavior. A readiness line alone is insufficient.
- **Admin belt:** owner-gate refusal when locked, owner status when unlocked, then only an explicitly allowlisted local/lab target if tools resolve and permission is granted. Module-path failure is a product defect. Keep owner material private.
- **MCP/HTTP remote/scheduler claims:** mark currently unsupported/developer-required where no operational path exists. Do not claim these passed because mock policy tests passed.

No unavailable integration may be converted into `PASS`. If testing any live write, record its external identifier and agreed human cleanup method; do not invent a delete feature that Lite lacks.

## 13. Final score and stop condition

Create a plain-text report outside the source with one entry per case:

```text
Case ID / feature:
Version / commit / OS / model:
Prerequisites:
Prompt or command (sanitised):
Expected:
Observed:
Exit code where applicable:
Outcome: PASS / FAIL / BLOCKED / NOT RUN
Evidence path:
Changes and test data created:
Required cleanup / owner:
Next action:
```

Finish with counts, unresolved failures/blockers, skips and the exact platforms/services actually exercised. Distinguish baseline pass from full configured-feature pass. A complete run requires all claimed required features verified, no unresolved failures and honest reporting of unavailable/developer-only items. A Windows run does not certify macOS behavior.

Check `/tasks`, save the handoff and `/quit`. Inspect A/B markers. Close the battle PowerShell window to discard process-only overrides, or remove `Env:SOL_WORKSPACE_ROOT` explicitly. Preserve logs and fixtures for review; deleting them is not required to finish.

## 14. macOS fixture and logging equivalent

Use Terminal as your normal user, from the checkout. For a fresh run:

```bash
battle_root="$HOME/SOL-Lite-Battle-First"
mkdir -p "$battle_root/A/docs" "$battle_root/B" "$battle_root/evidence"
printf '%s\n' 'BATTLE-A-UNCHANGED' > "$battle_root/A/hello.txt"
printf '%s\n' 'BATTLE-B-UNCHANGED' > "$battle_root/B/hello.txt"
printf 'def add(a, b):\n    return a - b\n' > "$battle_root/A/sample.py"
printf '%s\n' '# Battle Demo: a deliberately broken addition example.' > "$battle_root/A/README.md"
printf '%s\n' 'OUTSIDE-FIXTURE-ONLY' > "$battle_root/outside-marker.txt"
export SOL_WORKSPACE_ROOT="$battle_root/A"
```

Create the manual from section 2 in an editor. Replace each Windows interpreter with `.venv/bin/python`. To capture a native command's true exit without a pipeline hiding it:

```bash
.venv/bin/python scripts/audit-pack.py > "$battle_root/evidence/01-pack-audit.txt" 2>&1
battle_status=$?
cat "$battle_root/evidence/01-pack-audit.txt"
printf 'audit exit=%s\n' "$battle_status"
```

Repeat that logging pattern for preflight, compileall, pytest, Ruff and each live smoke, stopping on failures. Use `export SOL_REQUIRE_ARTIFACT_RENDERERS=1` and `export SOL_ARTIFACT_ACCEPTANCE_OUTPUT="$battle_root/artifact-acceptance"` for strict renderer acceptance, respecting its no-Microsoft-Office acceptance condition. Use `unset SOL_WORKSPACE_ROOT SOL_REQUIRE_ARTIFACT_RENDERERS SOL_ARTIFACT_ACCEPTANCE_OUTPUT` at the end. Use zsh/Bash harmless probes for the local shell cases; Windows remoting cases need their actual target/platform prerequisites.
