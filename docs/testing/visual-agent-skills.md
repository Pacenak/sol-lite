# Visual skills: testing and acceptance

## Executed round — 17 October 2026, Pacific/Auckland

Tested the shared Windows checkout using its `.venv` Python 3.13 environment. This is a working-tree snapshot, not a clean release or deployed application certification. Other changes were present and the shared tree changed during the round; full-suite failures cannot be attributed to the visual integration from this run alone.

Results:

- Final focused regression: **42 passed, 7 skipped**. Covers skill discovery, all standard agent personas, mixed visual intent injection, substring boundaries, explicit invocation, workspace manifest discovery, invalid trigger metadata, artifact tools, workspace answers and skill network gating.
- Focused Ruff check: **passed** for `src/sol_lite/skills/manager.py` and `tests/unit/test_skill_manager.py`. The round corrected an invalid-type exception to `TypeError` and added a regression test for YAML arrays in trigger metadata.
- All three visual manifests passed the skill-creator validator in the preceding integration round. This round re-parsed them through the actual harness, confirmed no inspection warnings, and parsed every fenced JSON/SVG example using Python's standard library.
- Full suite with temporary storage outside the repository: **496 passed, 7 failed, 11 skipped, 3 errors** in 17.10 seconds. This run preceded the final invalid-metadata test; the final focused run includes that test.
- Earlier full run with temporary workspaces inside the repository: **354 passed, 27 failed, 11 skipped, 3 errors**. Several shell fixtures unexpectedly detected the outer Git root and requested interactive input. The outside-repository rerun reduced that environmental interference. The differing totals also reflect concurrent working-tree changes; they are not a controlled before/after comparison.
- Preflight: **failed**, `expected 39 built-in skills, found 45` at the time of execution.
- Pack audit: **failed**, reporting files absent from the build manifest and numerous hash mismatches across the current tree. Release hashes were not regenerated to conceal these failures.

The seven skips in the focused run are optional `docx`, `pptx` and `openpyxl` authoring checks. Full-suite skips additionally cover unavailable symlinks, the opt-in real artifact renderer test and a Linux-only execution test. No actual PPTX/PNG export, Excalidraw application import, browser visual inspection, Ollama conversation, remote renderer or PLG_Ai_Interface live integration was certified by this round.

## Full-suite failures requiring separate investigation

- `test_ping_and_http_use_fixed_targets`: expected reachability was false.
- `test_bootstrap_wires_agent_harness` and `test_bootstrap_is_not_cwd_dependent`: Windows Credential Manager `CredRead` returned access denied.
- `test_json_invalid_event[start-2026-02-30T20:00:00Z]`: the expected validation error was not raised.
- `test_env_for_brain_sets_roots` and `test_settings_file_when_present`: network access was denied while probing a configured UNC repository path.
- `test_help_documents_enter_to_send_and_shift_enter_to_edit`: help output lacked the asserted `approval popup` text.
- Three `test_repository_pull_merge.py` setup errors: fixture `git push -u origin main` exited 128. The captured summary does not establish the underlying Git failure reason.

These remain open findings; this documentation update does not claim they were repaired.

## Reproduce automated checks

Use an isolated writable temporary directory **outside any Git repository** to avoid unintended root-selection prompts. Set both Python's temporary directory and pytest's base directory. Pick a fresh disposable path: pytest may clear an existing base directory.

```powershell
# Example: substitute an absolute, writable, non-repository directory.
$visualTestRoot = Join-Path $env:LOCALAPPDATA 'SOL-Lite-VisualTests'
New-Item -ItemType Directory -Force -Path $visualTestRoot | Out-Null
$env:TEMP = $visualTestRoot
$env:TMP = $visualTestRoot

.venv/Scripts/python.exe -m pytest tests/unit/test_skill_manager.py tests/unit/test_artifacts.py tests/unit/test_workspace_answer.py tests/unit/test_skill_network_gate.py -q --basetemp="$visualTestRoot/focused" --tb=short
.venv/Scripts/python.exe -m ruff check src/sol_lite/skills/manager.py tests/unit/test_skill_manager.py
.venv/Scripts/python.exe -m pytest -q --basetemp="$visualTestRoot/full" --tb=short
.venv/Scripts/python.exe scripts/preflight.py
.venv/Scripts/python.exe scripts/audit-pack.py
```

Temporary environment changes affect the current shell session. Run each command separately and retain its exit code/output. The preflight and audit are independent release gates; passing focused tests does not override them.

Local evidence logs from this round are under `workspace/`: `visual-docs-full-tests.log`, `visual-docs-external-temp-tests.log`, `visual-docs-preflight.log`, and `visual-docs-audit.log`. These are local working artifacts, not a committed CI record.

## Renderer and agent acceptance

Use a fresh workspace and versioned output directories. Complete each step on every supported target OS with the intended agent configuration.

1. Run `/skills list` for PA, Business, Docs and Engineer. Confirm the three visual skills appear. Request a combined diagram/deck/code-frame task; verify all requested editable sources are returned rather than only one capability.
2. With optional tools absent or intentionally unavailable in an isolated environment, request Mermaid + SVG, Marp + HTML and a code frame + layout JSON. Verify usable fallbacks, no package downloads, no false PNG/PPTX claims and no remote uploads. Do not uninstall shared tools just to simulate this case.
3. With installed tools and intended command permissions, generate a flowchart and sequence diagram. Export SVG/PNG through Mermaid; inspect every label and edge. Generate an Excalidraw scene and import it in the application. Record actual import success separately from JSON validity.
4. Generate a short Marp deck in Markdown, offline HTML, PPTX and PNG. Inspect every slide for overflow, typography, contrast and aspect ratio. Record that normal Marp PPTX is image-based. Separately request native editable text slides when `python-pptx` is available and verify text editability in a compatible editor.
5. Test code containing `<`, `&`, quotes, tabs and long lines. Confirm escaping preserves the code and the frame stays readable. Test a portrait image and screenshot annotations with known source coordinates; confirm contain-fit, orientation and transformed annotation bounds. Export PNG with the installed exporter and verify signature/dimensions.
6. Repeat long labels, dense slide content, 4:3 slides, 16:9 diagrams, square and 4:5 markup, transparent backgrounds and missing source images. The agent should split or resize deliberately and report missing inputs or exports.
7. If a container/service is configured, test its documented contract, credentials, failure response and local fallback. A configured endpoint is a prerequisite; the Interface bridge alone is not a renderer.
8. Record prompt, active agent/workspace, dependency versions, outputs, structural checks, screenshots, visual findings and remaining issues. Mark acceptance complete only for formats actually exported and inspected.

See [operator guide](../user/visual-agent-artifacts.md) and [integration details](../integrations/visual-agent-skills.md).
