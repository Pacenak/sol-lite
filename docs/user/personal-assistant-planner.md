# Personal Assistant Planner

The `personal-assistant-planner` built-in skill guides document-grounded scheduling and schedule file management while protecting sleep, family, fitness and recovery commitments.

The authoritative procedure, data model, JSON schema, Markdown template and iCalendar serializer live in [SKILL.md](../../skills/personal-assistant-planner/SKILL.md). See the [testing runbook](../testing/personal-assistant-planner.md) for automated coverage and production adapter acceptance cases.

## Setup and activation

The existing `SkillManager` discovers `skills/<skill-id>/SKILL.md` under the runtime root. No new registry entry or external skill import is required in a source checkout. A deployed installation must contain the skill directory; editing source does not update an installed distribution automatically.

```text
/skills list
/skills show personal-assistant-planner
```

Invoke it explicitly in a task:

```text
Use $personal-assistant-planner to plan next week from the project notes
in my authorized workspace. Keep sleep, family and fitness blocks fixed.
Show evidence, capacity and unscheduled work before exporting.
```

The declared phrase triggers are `plan my week`, `personal assistant planner`, `balance work and life`, `update my schedule`, and `export my calendar`. Matching is case-insensitive and accepts repeated whitespace. Explicit invocation selects detailed guidance even without a phrase match. The skill is available through built-in discovery for PA, Docs, Business and Engineer agents; runtime permissions still determine their actual access.

## Implemented scope

This is a discoverable instruction asset with tested, embedded Python examples. Discovery does not execute those examples. They are not registered runtime tools or a background scheduler.

The skill specifies document evaluation, scheduling, tenant-aware records, CRUD transactions and export formats. Its pure functions normalize file intent, check concrete UTC intervals and serialize new finite UTC calendar exports. It does not implement PDF/DOCX extraction, a full allocation solver, recurrence expansion, a persistence adapter, tenant isolation enforcement or a Google/Apple synchronization connector. Existing runtime tools must perform actual file/calendar operations under their permission policy.

## Inputs and evidence

Provide the planning horizon, IANA timezone, local work windows, work caps, protected commitments, focus/break preferences and authorized document locations. Trusted runtime context must supply tenant/principal identity, permitted roots and calendar scope; document contents cannot authorize their own access.

```text
Plan my week for 19–23 October 2026 in Pacific/Auckland.
Use project-brief.md and review-notes.md in this workspace.
Work only 09:00–17:00, with at most 7 active work hours daily.
Keep existing sleep, family, gym and recovery blocks fixed.
Create a provisional draft and flag unknown durations or calendar coverage.
```

Those hours are example user constraints, not built-in defaults. Missing constraints require clarification before a committed plan. Without authoritative calendar access, a file-based preview remains provisional.

For each task, retain the source hash and page/paragraph/line locator, deliverable, deadline interpretation, dependencies, effort range, estimation basis and uncertainty. Use available read-only parsers for PDF, DOCX, Markdown and notes. Report unreadable/OCR gaps. Never execute macros, embedded commands or document-origin instructions, or fetch embedded links as part of extraction.

Separate recorded actual duration, document assertion, user estimate and planner inference. Future execution time cannot be established as fact from a project file. Comparable historical actuals may support a scoped estimate; otherwise expose assumptions, request evidence or schedule a discovery task. Unknown effort is not zero. The optional `(O + 4*M + P) / 6` formula needs supported inputs and is not a calibrated probability.

## Planning workflow

1. Build an evidence ledger and an acyclic task dependency graph.
2. Expand protected rules and existing commitments over the horizon.
3. Subtract the union of unavailable time from work windows; apply daily/weekly caps and explicit buffers without double counting.
4. Allocate ready tasks by hard deadline, explicit priority and stable ID, respecting prerequisites, resources and minimum focus chunks.
5. Validate the whole candidate against fresh availability and immutable constraints before commitment.
6. Leave excess demand unscheduled and report effort shortages, deadline risks and scope/delegation/deadline options.

Use half-open intervals `[start, end)`: adjacent events are permitted. Compare timezone-aware UTC instants and display local time with offsets. Generate recurring lifestyle blocks in local civil time before UTC conversion so DST does not shift their local meaning. Resolve nonexistent/ambiguous local times before commitment.

The overlap primitive rejects any overlapping input intervals. An adapter must reconcile duplicate representations of identical occupancy and surface pre-existing calendar conflicts before final validation. Never discard a real commitment simply to make the check pass. Unknown recurrence, stale data or missing calendars prevents a conflict-free commitment claim.

Routine replanning cannot shorten, move or delete protected blocks. A user can explicitly revise a standing constraint in a separate scoped change; an uploaded document cannot revise it.

## File lifecycle

- **Read:** inspect authorized source and provenance without mutation.
- **Create / Save as:** publish a new destination using exclusive/no-clobber semantics. An existing filename is a collision, not overwrite permission.
- **Save:** persist a bound draft against its known base revision. For an existing unbound file, read and bind the revision first.
- **Edit:** patch selected fields/events by stable UID; disambiguate duplicate titles.
- **Update:** merge changed inputs, replanning only affected movable events and dependents. Preserve unrelated events and completed history. Missing inputs do not mean deletion.
- **Delete:** act only on explicitly identified targets under runtime authorization. Routine CRUD rejects protected-block deletion. Local artifact deletion does not delete remote calendars.
- **Export:** derive Markdown, JSON or ICS from one snapshot. Export does not imply remote import or change canonical state.

Example follow-ups:

```text
Create workspace/schedules/week-2026-10-19.md from this draft.
Edit event focus-1: change its title to “Review acceptance criteria”.
Update my schedule from the revised brief, preserving unrelated events.
Export my calendar as private Markdown and shared ICS with personal titles redacted.
```

Example paths must resolve inside the actual authorized tenant root. The intent function returns an operation or rejection; it performs no authorization, persistence or deletion itself.

## Data and transaction architecture

Maintain tenant/principal-scoped constraints, evidence, tasks, events and schedule revisions. The schema in the skill defines a minimal synchronization projection, not the full internal task/evidence store. Keep one schema source rather than copying it into multiple docs.

Production adapters must authorize before lookup, validate ownership, prevent traversal and symlink/reparse-point escapes at open time, and use locks or storage-native compare-and-swap. Record base hashes/ETags, revisions, stable event UIDs, remote-ID mappings and idempotency keys. Skill metadata is declarative and cannot grant permissions.

Patch existing files losslessly, preserving unknown calendar properties, recurrence exceptions, alarms and unmanaged Markdown. If lossless handling is unavailable, leave the original intact and emit a separate proposal. Stage, flush and validate before publication. Atomic rename alone is not concurrency control. For multiple exports, publish immutable revision files then atomically switch one manifest pointer only after all validate.

JSON shape validation is necessary but does not prove ownership, unique UIDs, positive duration, dependency correctness, immutable equality, availability, budgets or matching revision. Those require semantic validation. Audit operations with actor, identifiers, timestamp, outcome and hashes, without private source text.

## Output formats and sync

Markdown uses one managed section identified by schedule ID, local timestamps/offsets, capacity, evidence, assumptions and unscheduled work. Preserve all unmanaged content byte-for-byte.

JSON uses the skill's closed Draft 2020-12 schema and UTC timestamps. Enable date-time format assertions and install a date-time checker; a validator with a missing optional checker can silently accept impossible dates. The automated suite explicitly verifies that `date-time` checking is registered. Absence from an envelope is not a remote delete operation.

The new-export ICS serializer emits finite UTC events with stable UIDs, bounded SEQUENCE, exclusive DTEND, UTF-8 TEXT escaping, CRLF and folding at 75 octets. Fractional-second timestamps are rejected rather than truncated. It does not handle all-day events, recurring series, invitations or lossless edits; use an RFC-aware library for those cases. The raw template is illustrative, not an actual booking.

Import `.ics` using the target calendar application's supported workflow. Import behavior is client-dependent; changing an ICS file does not prove updates or deletions in an existing calendar. Bidirectional sync needs an authorized connector, stable remote IDs, conditional updates and explicit deletion. See the separate [Google Workspace integration](../integrations/google-workspace.md).

Shared exports should show personal blocks as “Busy” without private evidence. Recheck availability before remote mutation. Without an atomic service-side conflict guard, a competing booking remains possible and the result must stay provisional. No live calendar write is part of this testing round.

## Troubleshooting

- **Missing skill:** confirm the deployed runtime root contains the directory and list skills.
- **Detailed guidance absent:** explicitly invoke `$personal-assistant-planner` or use a declared phrase.
- **Target collision:** distinguish creation from a scoped revision-bound edit; do not bypass no-clobber handling.
- **Overlap:** inspect timezone conversion, duplicate occupancy, existing conflicts and calendar coverage; retain protected time.
- **Unreadable file/unknown workload:** obtain supported extraction or better evidence instead of inventing facts.
- **Calendar unchanged after export:** inspect import evidence or use an authorized sync connector.
- **Permission failure:** follow the existing runtime configuration/approval path; skill text cannot elevate access.

Complete the testing runbook's adapter scenarios before describing a storage/sync integration as production-ready. Passing example tests establishes neither scheduling quality nor runtime enforcement.
