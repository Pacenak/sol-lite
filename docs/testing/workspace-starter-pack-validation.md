# Workspace starter pack Stage 1 — implementation and validation

Date: 2026-10-19. Baseline: local SOL-Lite v0.2.6,
commit `c6bfce4bb3a6b36de83e466882a824aaa6101b40`.
The user explicitly authorized this local checkout as authoritative after
GitHub access failed. No equivalence to a remote GitHub revision is asserted.

The original specification is retained unchanged at
`docs/design/2026-10-19-workspace-starter-pack-design.md`. Its contents are
design input; the user's request and subsequent authorization define the work.
The requested `using-superpowers` and `system-design` skills were unavailable;
source inspection and the available readable-plans guidance were used instead.

## Integration coverage

- `workspace_pack/pack.py` owns guarded inspection, code-defined templates,
  fixed core/project interviews, optional two-question followups, marked README
  updates, project discovery, index reconciliation, PLAN parsing and append writers.
- `workspace_pack/context.py` reads INDEX first and README second before model
  work. Contents enter a user-role reference message explicitly marked untrusted,
  never the shell's trusted system prompt. Large content is visibly truncated.
- `tools/workspace_pack.py` supplies five native tools, code-enforced role checks,
  explicit read/write permission checks, complete batch proposals and exact
  approval retry handling. A bounded, expiring process-local proposal cache
  retains generated timestamps while approval is pending; it grants no authority.
- The existing notes tool name and content-only model schema remain intact.
  Notes now share pack storage, full legacy notes import once, and original
  notes files remain untouched. The legacy memory utility remains available
  for compatibility but is no longer the live tool's write destination.
- Four `tools.yaml` files grant the correct tools. Four prompts and the built-in
  `workspace-pack` skill state the pack conventions. No agent registry format
  change or skill catalogue release change is required by the actual source.
- Task fit exposes pack setup only for matching requests or an ongoing PA
  interview. Status and logging support other tasks. Status supplies workspace
  evidence; successful pack mutations count as change evidence only when they
  actually report written files. The existing notes gate remains intact.
- Generic filesystem write/edit handlers reject managed pack paths, including
  case variations on Windows. Native pack writers validate containment and
  reject symlink/reparse aliases. PLAN and shared logs append without rewriting
  existing bytes. README/intake/index replacements use same-directory temporary
  files and atomic replacement after preflight.
- Source-pack audit now excludes `.work` scratch output and the portable
  runtime workspace, and prunes excluded trees instead of recursively scanning
  them. This avoids shipping generated workspaces and build/test scratch data.

## Explicit format resolutions

The design requires both grouped PLAN entries and append-only writes. When
switching between tasks and routines, the writer appends the corresponding
section heading. The parser accepts repeated section headings, reserves
malformed existing IDs and reports line-numbered errors without rewriting
source entries. A future Stage 2 reader must use the same parser contract.

The notes input schema does not classify prose into description versus tips.
To preserve every supplied word without model inference, the wrapper quotes
the complete note into the README editing section and into shared tip entries
of at most five lines. Legacy import also splits long text into entries of
at most five lines. No supplied content executes or grants permissions.

Removed index rows use `(removed)` in the type column and retain their original
purpose text for that cycle. A second refresh drops them; status inspection
does not advance the cycle. Intake values for planning and note style are also
included in managed convention regions, so all seven core answers influence
the rendered pack rather than disappearing after the interview.

## Checks performed

- Final focused suite: **61 passed, 1 skipped**. It covers the new pack,
  scripted model integration, task fidelity, runtime safety, allowlists,
  project-brief behavior, registry and source-audit exclusions. The skip is the
  symlink creation test: this Windows session lacks symlink privileges.
- Existing workspace/notes answer regressions: **16 passed, 1 deselected**.
  The deselected skill-selection failure is independently reproduced on baseline.
- Golden files compare all six rendered pack documents, including a skipped
  answer and its `needs-info` task, under a fixed timestamp.
- Real tool dispatch with a stubbed model completes status inspection, seven
  saved answers and initialization through the approval engine. A subsequent
  turn verifies INDEX-before-README ordering outside trusted system policy.
- `python -m compileall -q src tests`: passed.
- Ruff on the new modules, notes integration, audit script and new tests: passed.
- Full repository Ruff: **25 findings**, matching the untouched baseline's
  25 findings. Existing findings are retained rather than silently reformatted
  across unrelated source files. Logs contain the exact rules and locations.
- Full pytest run: **564 passed, 27 failed, 12 skipped, 3 errors** across
  606 collected cases at that point. This is not a passing full suite. Final
  relevant checks above were rerun after subsequent pack refinements and the
  additional source-audit test; a second full-suite pass is not claimed.

## Baseline comparison and limits

A separate clean extraction of the baseline commit was used to rerun the
existing failing groups. It reproduced **25 failures** in shell/flare,
skill import, voice and unrelated skill selection; an additional baseline
run reproduced the fixed-target ping failure and all **3 repository fixture
errors**. This accounts for 26 of the final full run's 27 failures and all
three errors. The remaining catalogue rollback failure was a Windows
`PermissionError` in unchanged catalogue code; that single test passed on
both the baseline and the updated tree when rerun separately.

Reported environmental failures include captured stdin during workspace Git
root prompts, denied sandbox temporary-directory operations, unavailable OS
voice output, fixed-target reachability and local Git push fixture failures.
The unrelated skill-selection assertion also fails on baseline. These are
recorded limitations, not successful checks, and are outside Stage 1 changes.

Live Ollama verification was not performed. Test the setup interview, normal
notes, project registration and approval denial with the actual local model
before relying on it for production workspace maintenance. Timestamp offsets
come from the host configuration. Cooperating writes are serialized only
within a SOL-Lite process, not across processes or multiple users. Approval
preflight is not a cross-file filesystem transaction; an OS error can leave a
partial batch, although existing update-mode files use atomic replacement.

## Delivery verification

Windows antivirus blocked and then removed an unchanged tracked upstream
security-training document during full-manifest construction:
`skills/ecosystem/cyber-detecting-fileless-malware-techniques-d292c534/UPSTREAM-SKILL.md`.
The host reported “contains a virus or potentially unwanted software.” No
antivirus setting was changed and the file was not restored or redistributed.
Its expected SHA-256 is available in its existing `provenance.json`; that
recorded digest is retained in the full-source manifest rather than invented.
Additional host-blocked baseline files, if encountered, are listed in the
inventory metadata and delivery receipt with their recorded provenance digests.
All delivered files are directly hashed and verified; none uses this fallback.
The full-source audit therefore remains blocked by the quarantined baseline
file, separately from the completed pack implementation and passing focused tests.

The overlay contains complete file contents with SOL-Lite-relative archive
paths. `WORKSPACE_STARTER_PACK_FILES.json` is the authoritative per-file
inventory, including original Git-blob digests and delivered digests.
Git normalizes text line endings, so original Git-blob hashes can differ from
an otherwise clean Windows worktree using CRLF. Delivered hashes and the full
build manifest use the exact authorized local checkout bytes.

The release process stages the available source baseline plus this overlay,
regenerates PROJECT_FILES and BUILD_MANIFEST, runs the source audit, extracts
the ZIP onto an isolated baseline copy, verifies every delivered digest and
reruns the audit and focused pack tests there. The audit is not called passing
when a baseline file is missing or unreadable. The delivery receipt beside
the ZIP records the exact outcomes, host-blocked files and archive checksum.

## Raw evidence

- `workspace-starter-pack/pytest-focused.txt`
- `workspace-starter-pack/pytest-full.txt`
- `workspace-starter-pack/pytest-baseline.txt`
- `workspace-starter-pack/pytest-baseline-extra.txt`
- `workspace-starter-pack/pytest-baseline-catalogue.txt`
- `workspace-starter-pack/ruff-full.txt`
- `workspace-starter-pack/ruff-baseline.txt`

## Delivered file inventory

The overlay contains **49 complete files**. Paths below are relative to the SOL-Lite base directory.

- `BUILD_MANIFEST.json` — replacement.
- `CHANGELOG.md` — replacement.
- `PROJECT_FILES.txt` — replacement.
- `WORKSPACE_STARTER_PACK_FILES.json` — addition.
- `WORKSPACE_STARTER_PACK_INSTALL.md` — addition.
- `docs/README.md` — replacement.
- `docs/design/2026-10-19-workspace-starter-pack-design.md` — addition.
- `docs/superpowers/plans/2026-10-19-workspace-starter-pack.md` — addition.
- `docs/testing/workspace-starter-pack-validation.md` — addition.
- `docs/testing/workspace-starter-pack/pytest-baseline-catalogue.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-baseline-extra.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-baseline.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-focused.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-full.txt` — addition.
- `docs/testing/workspace-starter-pack/ruff-baseline.txt` — addition.
- `docs/testing/workspace-starter-pack/ruff-full.txt` — addition.
- `docs/user/workspace-starter-pack.md` — addition.
- `scripts/audit-pack.py` — replacement.
- `skills/workspace-pack/SKILL.md` — addition.
- `src/sol_lite/agents/business/prompt.md` — replacement.
- `src/sol_lite/agents/business/tools.yaml` — replacement.
- `src/sol_lite/agents/docs/prompt.md` — replacement.
- `src/sol_lite/agents/docs/tools.yaml` — replacement.
- `src/sol_lite/agents/engineer/prompt.md` — replacement.
- `src/sol_lite/agents/engineer/tools.yaml` — replacement.
- `src/sol_lite/agents/pa/prompt.md` — replacement.
- `src/sol_lite/agents/pa/tools.yaml` — replacement.
- `src/sol_lite/agents/runtime.py` — replacement.
- `src/sol_lite/agents/shell.py` — replacement.
- `src/sol_lite/agents/task_fit.py` — replacement.
- `src/sol_lite/permissions/scopes.py` — replacement.
- `src/sol_lite/tools/__init__.py` — replacement.
- `src/sol_lite/tools/filesystem.py` — replacement.
- `src/sol_lite/tools/notes.py` — replacement.
- `src/sol_lite/tools/workspace_pack.py` — addition.
- `src/sol_lite/workspace_pack/__init__.py` — addition.
- `src/sol_lite/workspace_pack/context.py` — addition.
- `src/sol_lite/workspace_pack/pack.py` — addition.
- `tests/fixtures/workspace-pack/golden/CHANGELOG.md` — addition.
- `tests/fixtures/workspace-pack/golden/CONVERSATIONS.md` — addition.
- `tests/fixtures/workspace-pack/golden/INDEX.md` — addition.
- `tests/fixtures/workspace-pack/golden/INTAKE.md` — addition.
- `tests/fixtures/workspace-pack/golden/PLAN.md` — addition.
- `tests/fixtures/workspace-pack/golden/README.md` — addition.
- `tests/integration/test_workspace_pack_runtime.py` — addition.
- `tests/unit/test_project_brief.py` — replacement.
- `tests/unit/test_registry.py` — replacement.
- `tests/unit/test_workspace_answer.py` — replacement.
- `tests/unit/test_workspace_pack.py` — addition.
