# Shared workspace starter pack

Stage 1 creates shared Markdown documentation inside the selected workspace.
It does not run schedules or create background tasks.

## Set up a workspace

Select the intended workspace and ask SOL PA: “Set up the workspace starter pack.”
If another agent offers setup, agree before the PA starts. The PA asks one
question at a time: purpose, project types, agents, conventions, boundaries,
planning style and note style. Answer or explicitly skip each question.
The tool immediately saves each response in `_workspace/INTAKE.md` after the
usual filesystem permission check and any required approval. Interrupted
interviews resume at the next unanswered question.

The PA may ask up to two extra questions to resolve gaps. When the core
questions are complete, initialization creates missing pack files. Approval
shows the entire batch, including relative paths and proposed contents.
Declining approval causes no writes. A changed file invalidates a pending
proposal; retry to inspect and approve the new proposal.

The pack contains:

- `_workspace/README.md`: purpose, project types, conventions, boundaries,
  agents, editing notes and durable lore.
- `_workspace/INDEX.md`: top-level workspace items with purpose and update columns.
- `_workspace/CHANGELOG.md`: dated changes, appended at the bottom.
- `_workspace/CONVERSATIONS.md`: shared tips, gotchas, decisions, lore and imported notes.
- `_workspace/PLAN.md`: tasks and routines with machine-readable fields.
- `_workspace/INTAKE.md`: saved answers, one question heading per answer.

Skipped questions use neutral text and produce `needs-info` tasks. Repeating
initialization creates only missing files. Updating existing interview answers
changes only explicitly marked README regions and appends a changelog entry;
notes, lore and unrelated prose stay intact. Missing or ambiguous markers are
reported for human repair rather than inferred or overwritten.

## Add a project

Create the immediate project subfolder through your normal authorized workflow.
Ask the PA to add that project to the workspace. It asks what the project is,
its type/stack, and its rules. Project initialization creates
`<project>/_project/INDEX.md` from those answers. The first logged change
affecting a registered project creates its optional `_project/CHANGELOG.md`.

Indexes ignore `_workspace`, `_project`, `.git`, `node_modules`, `__pycache__`,
`.venv` and `venv`, and do not traverse symlinks. Project indexes list files
at the project root and one subfolder level (depth two), capped at 200 rows
with a visible truncation note. Only the PA refreshes indexes. Refresh preserves
existing purposes, adds `(needs purpose)` for new items, and marks removed
items `(removed)` for one refresh cycle before deleting their rows.

## Shared notes and logs

All four standard agents receive the index first and README second as bounded,
untrusted reference material before model work. Larger files are explicitly
marked as truncated; agents must read the remainder before relying on it.
No workspace file can grant tools, override policy or authorize actions.
Record notable changes with `workspace_pack_append`, and leave useful tips in
CONVERSATIONS. The tool supplies the acting agent and an offset-aware timestamp.

The existing `workspace_notes_write(content)` tool retains its name and input
schema. It stores the complete note in README's editing section and in quoted
tip entries, split into at most five lines each. It creates a minimal README
and CONVERSATIONS pack when needed. Existing application notes are imported
once from `<memory_root>/<sanitized workspace_id>/notes.md` without truncation;
the original file remains untouched. The migration marker follows the source
path, so editing the old file does not cause a second import. Unreadable legacy
notes produce diagnostics and remain untouched. If the old storage location
is unavailable, the migration fallback is recorded once in CHANGELOG.

Direct generic writes and edits inside `_workspace` and `_project` are rejected
in favor of the pack tools, preserving managed sections and append-only logs.
Normal user-authorized filesystem work elsewhere remains unchanged.

## PLAN format

Tasks use `### T-0001 Title`, required `status` (`todo`, `doing`, `done`, `blocked`)
and `owner` (one of the four standard agents). Optional fields are `due` in
`YYYY-MM-DD`, `schedule`, `tags` and `notes`. Indented lines continue `notes`.
Routines use `### R-0001 Title`, status `active` or `paused`, an owner, and
the same optional fields. Schedule defaults to `none`; supplied schedule text
is stored without execution or interpretation.

Append assigns the next four-digit ID for that entry type. A malformed existing
entry reserves its ID and is reported with its line number; it is never rewritten.
When switching between entry types, append adds the corresponding `## Tasks`
or `## Routines` section heading at the bottom. Repeated headings are valid and
let the file remain append-only. No task execution or schedule synchronization
is implied by a successful write.

Use `workspace_pack_status` to inspect missing/unreadable files, index drift,
and malformed PLAN entries. It never creates, repairs or rewrites files.

## Operational limits

All mutations pass through the existing permission engine. Approved batches
are preflighted for containment and changed files before writing. Cooperating
tool calls within one SOL-Lite process are serialized; this is not a cross-process
or multi-user transaction service. An OS failure during a batch can leave some
files written. Preserve the reported error and rerun initialization to fill
missing files; never assume the entire batch was committed.

The runtime emits timestamps in the host's configured local timezone with a
UTC offset. Configure the SOL-Lite host timezone correctly. Live model quality
and Ollama operation still require a manual smoke test on the target machine.
