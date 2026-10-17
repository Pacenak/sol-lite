# Personal Assistant Planner testing

The [skill](../../skills/personal-assistant-planner/SKILL.md) is an instruction asset containing Python examples and payload templates. Tests execute those trusted repository examples, exercise the real skill manager, validate JSON with an independent schema library and parse exports with an independent calendar library. They do not implement a storage adapter or contact live calendars.

## Reproduce

From the repository root with Python 3.11+:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit/test_personal_assistant_planner.py tests/unit/test_skill_manager.py tests/unit/test_skill_network_gate.py -q
python -m ruff check tests/unit/test_personal_assistant_planner.py
```

In the Windows checkout use `.\.venv\Scripts\python.exe` instead of `python`. If the sandbox cannot create its default pytest temp directory, pass a new workspace-local `--basetemp=workspace/<unique-test-directory>`. Pytest may delete an existing base directory; always choose a fresh disposable directory.

Development dependencies include `jsonschema>=4.23`, `rfc3339-validator>=0.1.4` and `icalendar>=6.0`. They are not runtime requirements. The explicit RFC 3339 dependency matters: enabling a format checker without its date-time implementation can silently skip validation. The suite asserts that this checker is active.

## Automated coverage

- Built-in discovery, no quarantine warnings, declared triggers, explicit invocation and unrelated-task exclusion across PA, Docs, Business and Engineer agents.
- Read/export/create/save/edit/update/delete intent transitions; filename collisions, missing revisions and ambiguous actions.
- Half-open adjacency, unsorted intervals, equivalent offsets, empty calendars, overlaps/containment, zero/negative durations and naive timestamps.
- Draft 2020-12 schema validity, a valid envelope, impossible dates, UTC requirements, required fields, closed object shape, UID injection, boolean types and bounded sequence numbers.
- Independent ICS parsing of the raw template and generated output; Unicode/TEXT round-trip, UTC instants, stable UID, unchanged inputs, CRLF, final newline and UTF-8 octet folding.
- Rejection of duplicate UIDs, UID injection, invalid controls, invalid sequence and fractional-second timestamps that would lose precision.

Adjacent skill-manager and network-gate tests provide regression coverage. They do not prove tenant isolation or transactional behavior for a planner adapter that has not been implemented.

## Production adapter acceptance

Use disposable tenant roots and authorized sandbox calendars. These scenarios are requirements for future adapters, not behaviors established by the pure examples:

1. Submit a valid tenant-A request naming tenant-B data. Reject before lookup/mutation; verify B's bytes remain unchanged.
2. Exercise traversal, symlink/reparse escapes and path swaps. Verify open-time containment.
3. Have concurrent writers patch one base revision. Permit one commit; require reconciliation for the other, preserving unrelated data.
4. Retry a successful request ID. Return the existing result without extra revisions or duplicate remote events.
5. Attempt to move, shorten or delete sleep/family/recovery blocks through update/delete. Reject and compare protected state before/after.
6. Import recurrence, EXDATEs, overridden occurrences, all-day and overnight events, including Auckland DST transitions. Verify occupancy and lossless unrelated edits.
7. Supply cyclic dependencies, unknown effort, contradictory deadlines and insufficient capacity. Return blockers and unscheduled work without fabricated duration or consuming protected time.
8. Include document-origin instructions and poor OCR in input documents. Verify extraction only, source locators and explicit uncertainty.
9. Inject staging/publication failures. Retain the last committed revision and clean only this transaction's staging files.
10. Export shared schedules. Verify private titles, document excerpts and constraint details are absent.
11. Test ETag conflicts, explicit remote deletion, partial sync failure and a competing booking between availability read and commit. Without an atomic conflict guard, do not claim guaranteed no double booking.
12. Import into Google/Apple test calendars and inspect local times, Unicode, deduplication and updates; repeated raw import is not assumed to synchronize.

Record fixture hashes, expected invariants, actual tool evidence, revisions and sandbox IDs per adapter case. Do not include credentials or private document text in reports.

## Recorded results

See [latest testing round](personal-assistant-planner-results.md) for executed checks and limitations, and the [user guide](../user/personal-assistant-planner.md) for operation and architecture.
