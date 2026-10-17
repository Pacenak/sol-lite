# Personal Assistant Planner: testing round

Executed on 17 October 2026 (Pacific/Auckland user date) in the Windows source checkout using its Python 3.13 virtual environment. The checkout contained other in-progress changes; this is not a clean-baseline comparison or a full release certification.

## Changes verified

- Added comprehensive user documentation, test instructions, adapter acceptance cases and documentation/catalogue links.
- Added `tests/unit/test_personal_assistant_planner.py`, which executes the trusted skill's embedded examples rather than a separate implementation.
- Added development-only validators: `jsonschema>=4.23`, `rfc3339-validator>=0.1.4` and `icalendar>=6.0`.
- Tightened the ICS example to reject fractional-second timestamps instead of losing precision and enforce SEQUENCE from 0 through 2147483647. The envelope schema uses the same sequence bound.

Installed independent validators for this round: jsonschema 4.26.0, rfc3339-validator 0.1.4 and icalendar 7.3.0. No runtime connector or external calendar was changed.

## Focused result: passed

**53 passed in 2.38 seconds**, comprising planner tests plus adjacent skill discovery/routing and network permission-gate regressions. No tests skipped in this focused run.

The final invocation redirected Python temporary directories into a fresh ignored workspace directory to avoid sandbox cleanup failures:

```powershell
@'
from pathlib import Path
import tempfile
import pytest
scratch = Path('workspace/pa-focused-temp-20261017-c').resolve()
scratch.mkdir(exist_ok=False)
tempfile.tempdir = str(scratch)
raise SystemExit(pytest.main([
    'tests/unit/test_personal_assistant_planner.py',
    'tests/unit/test_skill_manager.py',
    'tests/unit/test_skill_network_gate.py',
    '-q', '--basetemp=workspace/pa-focused-round-20261017-c', '--tb=short'
]))
'@ | .\.venv\Scripts\python.exe -X utf8 -
```

Choose new disposable names when rerunning this exact wrapper. It intentionally refuses to reuse the scratch directory.

Verified real harness discovery and detailed instruction routing across four agents; intent collision/revision guards; interval overlap rejection and adjacency; schema shape and impossible date rejection; independent calendar parsing of template/generated payloads; UID and UTC instant preservation; Unicode TEXT round-trip; CRLF and UTF-8 octet folding; invalid controls, duplicate IDs, sequence bounds and timestamp precision rejection.

Ruff passed for the new test file. The skill-creator `quick_validate.py` passed with Python UTF-8 mode. `git diff --check` passed for tracked changes; Git printed line-ending conversion warnings but no whitespace errors. These static checks do not establish production adapter behavior.

## Findings corrected during the round

The initial schema test accepted an impossible calendar date even with `FormatChecker()` enabled. The base jsonschema installation lacked its optional date-time checker. Added the explicit RFC 3339 development dependency and a fixture assertion that `date-time` is registered, then verified rejection of 30 February.

The original ICS timestamp formatter could silently truncate fractional seconds. It now rejects such input, preventing a short positive interval from exporting as zero duration. Invalid sequence values outside the RFC signed integer range are also rejected. These cases are covered by automated tests.

Initial pytest setup and ZIP traversal regression cleanup encountered sandbox default-temp access errors. The final focused run redirected both pytest's base temp and Python's `tempfile.tempdir`; all focused tests then passed. No product permission checks were bypassed to obtain that result.

## Broader unit run: not a release pass

The expanded command used `pytest.main(['tests/unit', '-q', '--basetemp=workspace/pa-unit-round-20261017-b', '--tb=short'])` with `tempfile.tempdir` set to a newly created `workspace/pa-test-temp-20261017-b` directory.

Result: **375 passed, 24 failed, 8 skipped, 3 errors in 8.85 seconds**.

Observed failure categories:

- Shell/flare/procedure tests attempted interactive repository-root selection while pytest captured stdin. Test fixtures inside this Git checkout contributed to that behavior. The runtime-context test also expected its temporary path while the runtime reported the enclosing repository root.
- Two portable-stick root tests encountered denied access to a configured network share.
- Three repository-pull/merge fixtures failed while running a local fixture `git push`; the captured summary establishes the subprocess failure, not its underlying cause.
- One terminal UI help assertion expected text absent from the rendered output. This was outside the planner changes and remains unresolved.
- Seven tests skipped because optional DOCX/PPTX/XLSX libraries were unavailable; one skipped because it requires Linux execution.

All planner tests passed in this broader run. Other failing modules were not modified to make the planner round green. Without an isolated baseline run, the broad failures must not all be labeled pre-existing regressions. Workspace-local temp handling makes this broad run environment-dependent.

## Remaining acceptance limits

No live Google/Apple import, remote update/delete, OCR/PDF/DOCX extraction, full scheduling-agent behavioral evaluation, tenant authorization enforcement, DST/recurrence adapter handling, lock/CAS transaction, protected-block persistence or rollback implementation was exercised. Those are specified requirements rather than implemented components of this skill asset.

Use the [adapter acceptance cases](personal-assistant-planner.md#production-adapter-acceptance) before production claims. This round validates discovery and deterministic examples; it does not certify end-to-end autonomous scheduling or the repository release gate.
