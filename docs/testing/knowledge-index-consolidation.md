# Knowledge index and inbox consolidation — validation and delivery

Date: 2026-10-19. Implementation baseline: the previously authorized local
SOL-Lite v0.2.6 checkout, Git commit
`c6bfce4bb3a6b36de83e466882a824aaa6101b40`, with the prior starter-pack changes.
GitHub DNS and browser retrieval both failed; remote main equivalence is not
asserted. The supplied design is retained byte-for-byte in `docs/design/` as
specification input, not independent authority to run instructions.

## Source verification and integration map

The seven verification items and full implementation route are recorded in
`docs/superpowers/plans/2026-10-19-knowledge-index-consolidation.md`.

- `src/sol_lite/tools/indexing.py` contains the complete pure parser, search,
  merge planner and assembler; contained sync handlers; two async wrappers;
  and three native tool definitions. No additional runtime package is required.
- `tools/__init__.py` aggregates the definitions. Capability metadata declares
  search/preview read-only and apply mutating. MCP discovers the same registry
  and retains its existing exposure/risk/authorization gates; no MCP policy
  broadening or separate server registration is necessary.
- Six agent `tools.yaml` files grant search to all existing agents and both
  consolidation tools only to PA and Docs. The handlers also enforce write roles.
- `agents/task_fit.py` routes retrieval and consolidation requests, retains
  allowlist intersection, and avoids interpreting a consolidation inbox as Gmail
  unless the request also explicitly mentions email/Gmail/calendar.
- `permissions/scopes.py` maps the new operation names to existing filesystem
  scopes. Apply binds paths, threshold, both expected hashes and the user's plan
  to the existing exact approval engine. An empty approval ID requests approval;
  it never spends an approval or bypasses policy.
- `agents/runtime.py` counts apply as change evidence only when `applied` is
  true. A no-op is not proof of a mutation. No paraphrase detector is added.
- `skills/knowledge-index/SKILL.md` directs exact quotation, conflict escalation
  and a separately approved pack log after successful apply. The old pack files
  retain their existing editing contracts and are excluded as merge targets.
- Preflight's existing built-in skill count is 56, matching the actual 54 baseline
  skills plus workspace-pack and knowledge-index. The verified complete preflight
  file is included so installation does not fail on the expanded skill set.

## Important implementation details

Physical lines split only on CRLF/LF/CR; strict UTF-8 is never replaced. BOM,
mixed original terminators and trailing-newline state are retained. BOM is
encoding metadata when prepending content, while search still returns the
exact decoded first-line text. Standard optional ATX closing hashes affect
header paths, without altering original citation/header lines.

Fences are atomic, section paths are normalized only for comparison, and any
conflict prevents a writable merge. The planner recognizes changed values,
ambiguous keys, ambiguous normalized headers, possible prose edits, and
unclosed fences. New table rows follow the last actual table rather than
unrelated prose containing a pipe. Existing target lines remain an identical
ordered subsequence of the assembled content, with encoding metadata handled
separately. Fresh hashes are rechecked around approval and replacement.

The 256-entry cache is lock-protected and never used by consolidation. Search
processes matching documents one at a time and retains only capped results;
it does not hold every matched parsed document outside the LRU. It still
counts all eligible matching blocks and reports truncation/incompleteness.
Header parsing and section-local search avoid rescanning the full header/hit
list for every section. Complex regexes use a conservative precheck when
whole-file matching would otherwise hide a valid per-line anchored match.

Source files are never changed. Only the existing target and a uniquely owned
temporary file are written. Failed atomic replacement cleans up only a temp
file actually created by this operation. Other processes do not participate
in the in-process apply lock; this is not a cross-process compare-and-swap
storage service. Avoid concurrent external editing while applying.

## Validation results

- New indexing unit/integration suite: **57 passed**.
- Final affected regression suite, including starter-pack behavior, task fit,
  allowlists and registry: **111 passed, 1 skipped** in 7.50 seconds. The skip
  is the pre-existing Windows symlink-creation privilege limitation. Link
  skip/ancestor handling also has direct deterministic tests without needing
  that privilege.
- The 2,000-file nonmatching Markdown smoke test completed in **3.31 seconds**
  including its test fixture creation. It verifies every file was scanned and
  no nonmatching file was parsed into physical lines. The search-only bound
  is 30 seconds; it passed.
- Scripted real-registry tests verify exact rendered retrieval and preview →
  exact approved apply → separately approved workspace-pack logging, plus role
  access, schemas, native risk metadata and MCP exposure policy.
- Async parity and apply-field validation pass through `asyncio.run` and
  `asyncio.to_thread`. The Windows sandbox initially blocked Python's event-loop
  localhost socket-pair setup; a stack trace identified the hang before any
  wrapper ran. The affected tests passed with that local facility available.
- `compileall -q src tests`: passed.
- Ruff on the new implementation/tests: passed. Full `ruff check src tests`:
  **25 pre-existing findings**, the same count and rules as the recorded baseline.
- Runtime preflight: **passed**, SOL-Lite 0.2.6, Rich 15.0.0, 56 built-in skills.
- Full repository suite: **629 passed, 21 failed, 12 skipped**. Every failed
  test name is present in the previously reproduced baseline failure set;
  no new failed test name remains. These are the documented shell/workspace Git
  root prompt/captured-stdin failures and unrelated skill-selection assertion.
  Full-suite execution preceded the final bounded-result and shared-boundary
  placement refinements; the final affected suite above verifies those refinements. A passing full suite
  is not claimed.

Raw logs are in `docs/testing/knowledge-index/`: `focused-pytest.txt`,
`full-pytest.txt`, `ruff-full.txt`, `ruff-new.txt`, and `preflight.txt`.

## Source-audit and live-model limits

The prior task's Windows antivirus quarantine still leaves this unchanged
baseline file unavailable:
`skills/ecosystem/cyber-detecting-fileless-malware-techniques-d292c534/UPSTREAM-SKILL.md`.
Its existing provenance digest is retained; it is not restored or distributed.
The audit is run against the resulting source tree and any nonzero result is
reported honestly in the delivery receipt. No passing full-source audit is
claimed while the baseline file is absent.

The full-source manifest updates the previous inventory for added/replaced
files; unchanged entries retain their previous recorded digests. Every file
actually delivered is directly hashed and compared after extraction. The
archive includes the prior starter-pack integration because updated shared
files reference it. No user workspace, inbox, credential, environment file,
runtime state or cache is shipped.

Live Ollama was not exercised. The tools provide deterministic output and
constraints, while the model's verbatim presentation remains skill guidance
as explicitly scoped in the design. Test the actual local model before using
this flow for production documentation maintenance.

## Complete delivered file list

This cumulative overlay contains **67 complete files**, including the required preceding starter-pack integration.

- `BUILD_MANIFEST.json` — replacement.
- `CHANGELOG.md` — replacement.
- `KNOWLEDGE_INDEX_FILES.json` — addition.
- `KNOWLEDGE_INDEX_INSTALL.md` — addition.
- `PROJECT_FILES.txt` — replacement.
- `WORKSPACE_STARTER_PACK_FILES.json` — addition.
- `WORKSPACE_STARTER_PACK_INSTALL.md` — addition.
- `docs/README.md` — replacement.
- `docs/design/2026-10-19-knowledge-index-consolidation-design.md` — addition.
- `docs/design/2026-10-19-workspace-starter-pack-design.md` — addition.
- `docs/superpowers/plans/2026-10-19-knowledge-index-consolidation.md` — addition.
- `docs/superpowers/plans/2026-10-19-workspace-starter-pack.md` — addition.
- `docs/testing/knowledge-index-consolidation.md` — addition.
- `docs/testing/knowledge-index/focused-pytest.txt` — addition.
- `docs/testing/knowledge-index/full-pytest.txt` — addition.
- `docs/testing/knowledge-index/preflight.txt` — addition.
- `docs/testing/knowledge-index/ruff-full.txt` — addition.
- `docs/testing/knowledge-index/ruff-new.txt` — addition.
- `docs/testing/workspace-starter-pack-validation.md` — addition.
- `docs/testing/workspace-starter-pack/pytest-baseline-catalogue.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-baseline-extra.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-baseline.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-focused.txt` — addition.
- `docs/testing/workspace-starter-pack/pytest-full.txt` — addition.
- `docs/testing/workspace-starter-pack/ruff-baseline.txt` — addition.
- `docs/testing/workspace-starter-pack/ruff-full.txt` — addition.
- `docs/user/knowledge-index-consolidation.md` — addition.
- `docs/user/workspace-starter-pack.md` — addition.
- `scripts/audit-pack.py` — replacement.
- `scripts/preflight.py` — replacement.
- `skills/knowledge-index/SKILL.md` — addition.
- `skills/workspace-pack/SKILL.md` — addition.
- `src/sol_lite/agents/business/prompt.md` — replacement.
- `src/sol_lite/agents/business/tools.yaml` — replacement.
- `src/sol_lite/agents/docs/prompt.md` — replacement.
- `src/sol_lite/agents/docs/tools.yaml` — replacement.
- `src/sol_lite/agents/engineer/prompt.md` — replacement.
- `src/sol_lite/agents/engineer/tools.yaml` — replacement.
- `src/sol_lite/agents/pa/prompt.md` — replacement.
- `src/sol_lite/agents/pa/tools.yaml` — replacement.
- `src/sol_lite/agents/rick_prime/tools.yaml` — replacement.
- `src/sol_lite/agents/runtime.py` — replacement.
- `src/sol_lite/agents/shell.py` — replacement.
- `src/sol_lite/agents/studio_admin/tools.yaml` — replacement.
- `src/sol_lite/agents/task_fit.py` — replacement.
- `src/sol_lite/permissions/scopes.py` — replacement.
- `src/sol_lite/tools/__init__.py` — replacement.
- `src/sol_lite/tools/filesystem.py` — replacement.
- `src/sol_lite/tools/indexing.py` — addition.
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
- `tests/integration/test_indexing_runtime.py` — addition.
- `tests/integration/test_workspace_pack_runtime.py` — addition.
- `tests/unit/test_indexing.py` — addition.
- `tests/unit/test_project_brief.py` — replacement.
- `tests/unit/test_registry.py` — replacement.
- `tests/unit/test_workspace_answer.py` — replacement.
- `tests/unit/test_workspace_pack.py` — addition.
