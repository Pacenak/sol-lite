# Workspace Starter Pack - Stage 1 Design

Date: 2026-10-19
Repo: Pacenak/sol-lite (v0.2.6)
Status: Draft for review (brainstorming complete, awaiting spec approval)
Stage: 1 of 2. Stage 2 (PLAN.md to scheduler sync) gets its own spec.

## 1. Purpose

Give the `sol_pa` agent the ability to create and maintain a standard
"starter pack" of shared documentation inside any workspace folder, and give
all four agents (`sol_pa`, `sol_business`, `sol_docs`, `sol_engineer`) the
knowledge to read and update it. The pack lets agents orient themselves, leave
notes for each other, and see what has happened over time.

### Success criteria

1. Asked to set up a workspace, the PA interviews the user, then creates a pack
   whose content reflects the answers.
2. Re-running setup never overwrites or loses existing files.
3. Every agent, on opening a workspace that has a pack, reads the pack index
   first and logs notable changes.
4. The existing `workspace_notes_write` tool writes into the pack, so there is
   one notes system, not two.
5. `PLAN.md` entries are machine-parseable so stage 2 can attach a scheduler
   without changing the format.
6. All writes obey the existing path guard and approval flow.
7. Works with small local Ollama models: structure, validation and question
   order are enforced in code, not trusted to the model.

## 2. Decisions already made

| Topic | Decision |
|---|---|
| Delivery | Code creates templates; a skill teaches conventions (no free-hand file layout by the model) |
| Base folder | Any folder the PA is pointed at; no assumption about layout |
| Pack location | Dedicated visible folder `_workspace/` at the workspace root |
| Template content | Generated from an intake interview with the user |
| Interview | Fixed core questions plus at most 2 PA-chosen follow-ups |
| Plan file | Stage 1 stores schedules; stage 2 syncs them to real background tasks |
| Existing notes tool | Absorbed into the pack |
| Scope | Two stages; this spec is stage 1 only |

## 3. Non-goals (stage 1)

- Executing or scheduling anything from `PLAN.md`.
- A scheduler, cron, or OS-level scheduling integration.
- Changes to `Session` or `Workspace` state in `core/session.py`.
- Multi-user conflict resolution beyond append-only rules.
- Voice, MCP or integration changes.

## 4. Pack layout

```
<workspace root>/
  _workspace/
    README.md          what the workspace is, project types, conventions, rules
    INDEX.md           index of top-level items in the workspace
    CHANGELOG.md       dated log of changes (append-only)
    CONVERSATIONS.md   agent-to-agent tips, gotchas, decisions, lore (append-only)
    PLAN.md            tasks and routines
    INTAKE.md          the user's interview answers (editable, re-runnable)
  <project>/
    _project/
      INDEX.md         files in this project with one-line purposes
      CHANGELOG.md     optional; created on the project's first logged change
```

A "project" is an immediate subfolder of the workspace root that either has a
`_project/` folder or was registered through the intake. The scaffolder ignores
`_workspace/`, `.git`, `node_modules`, `__pycache__`, `.venv` and `venv` when
building indexes.

### 4.1 File contracts

Every file begins with an HTML comment stating its purpose and editing rules,
so a model editing the file sees the rules in context.

**README.md** sections: `Purpose`, `Project types`, `Conventions`,
`Never touch / ask first`, `Agents and roles`, `What this is and how to edit it`
(the section the notes tool writes to), `Lore` (durable items distilled from
`CONVERSATIONS.md`).

**INDEX.md** is a single table: `| path | type | purpose | updated |`.
- Owned by `sol_pa`. Other agents may note a change in `CHANGELOG.md`; the PA
  reconciles the index through `workspace_pack_index_refresh`.
- Refresh adds rows for new items with purpose `(needs purpose)`, marks removed
  items `(removed)` for one cycle then deletes them, and preserves any existing
  purpose text.
- Per-project index lists files to depth 2, capped at 200 rows, with a
  truncation note if capped.

**CHANGELOG.md** entry format (append-only, newest at bottom):
```
## 2026-10-19T14:32:00+13:00 | sol_engineer
- Changed: <one line>
- Files: <comma-separated relative paths>
```

**CONVERSATIONS.md** entry format (append-only):
```
## 2026-10-19T14:35:00+13:00 | sol_docs | tip
<one to five lines>
```
Tags: `tip`, `gotcha`, `decision`, `lore`, `migrated`.

**PLAN.md** structure:
```
## Tasks
### T-0001 Title of the task
status: todo | doing | done | blocked
owner: sol_pa
due: 2026-10-25
schedule: none
tags: needs-info
notes: free text, may continue on following indented lines

## Routines
### R-0001 Title of the routine
status: active | paused
owner: sol_pa
schedule: every weekday 09:00
notes: what the routine should do
```
Rules: `status` and `owner` required; `due`, `schedule`, `tags`, `notes`
optional; `schedule` defaults to `none`; ids are `T-` or `R-` plus four digits,
assigned by the tool as max existing id plus one. In stage 1 `schedule` is
stored and never executed. An entry that does not parse is reported and left
untouched, never rewritten.

## 5. Intake interview

### 5.1 Core questions (fixed, in code)

| id | Question |
|---|---|
| purpose | What is this workspace for? |
| project_types | What kinds of projects will live here? |
| agents | Which agents do you expect to use it, and for what? |
| conventions | Any naming or folder conventions agents should follow? |
| boundaries | Is there anything agents must never touch, or must ask before changing? |
| planning_style | How do you like to plan: ad hoc, daily, weekly, or routines? |
| note_style | What tone or style should agents use in notes? |

The PA may add at most 2 follow-up questions, each recorded under id
`followup_1` and `followup_2`, chosen only from gaps in the user's answers.

### 5.2 Flow

1. The intake tool returns the next unanswered question; the PA asks it in chat,
   one question per message.
2. The tool records each answer in `INTAKE.md` immediately, so an interrupted
   interview resumes at the next unanswered question.
3. A user may skip a question. Skipped questions get neutral defaults in the
   rendered files and each produces a `T-` entry tagged `needs-info` in
   `PLAN.md`.
4. When all questions are answered or skipped, the PA calls
   `workspace_pack_init`, which renders the templates from `INTAKE.md`.
5. A new project triggers a mini-intake of 3 questions (`what`, `type_stack`,
   `rules`) that seeds `<project>/_project/INDEX.md`.
6. Re-running the interview updates `INTAKE.md`, re-renders only the
   intake-derived sections of `README.md`, and logs the change in
   `CHANGELOG.md`.

`INTAKE.md` format: one `### <question id>` heading per question, the answer
below it, and `skipped` for skipped questions.

## 6. Components

Module and file names are provisional until the verification items in section
10 are resolved.

### 6.1 Scaffolder (`workspace_pack` module)

Pure-Python, no model involvement.
- `inspect(root) -> PackState`: which pack files and projects exist.
- `render(intake, state) -> dict[path, content]`: fills packaged templates.
- `init(root, intake)`: writes only files that do not exist; returns lists of
  created and skipped files. Rendering of intake-derived README sections on
  re-run replaces only those marked sections.
- `append(root, kind, fields)`: append-only writers for `changelog`,
  `conversation`, `plan_task`, `plan_routine`; validates tags, status values and
  id assignment; timestamps and agent name are supplied by the tool, not the
  model.
- `index_refresh(root, project=None)`: reconciles an `INDEX.md` as described in
  section 4.1.
- All paths pass through `security/path_guard.py`; any path resolving outside the
  workspace root is rejected before any write.

### 6.2 Tools

| Tool | Agents | Purpose |
|---|---|---|
| `workspace_pack_status` | all | Read-only: pack state, index drift, unparsed plan entries |
| `workspace_pack_intake` | sol_pa | Return next question; record an answer or a skip |
| `workspace_pack_init` | sol_pa | Create missing pack files from the intake |
| `workspace_pack_append` | all | Append a changelog, conversation or plan entry |
| `workspace_pack_index_refresh` | sol_pa | Reconcile `INDEX.md` files |
| `workspace_notes_write` (existing) | all | Wrapper over the pack, see 6.5 |

Mutating tools go through the existing permission engine and human approval.
`workspace_pack_init` presents the full list of files it will create in one
approval request where the engine allows batching.

### 6.3 Built-in skill `workspace-pack`

Assigned to all four agents. States: read `_workspace/README.md` and `INDEX.md`
first; respect the `Never touch / ask first` rules; log notable changes with
`workspace_pack_append`; leave tips in `CONVERSATIONS.md`; only the PA
refreshes the index; offer pack setup when a workspace has none, and wait for
the user's yes. The skill is guidance only. Every hard rule it describes is also
enforced by the tools.

The skill and its trigger phrases must avoid the words "procedure", "checklist"
and "runbook", which trip the runtime's procedure-claim check.

### 6.4 Runtime hooks

- `task_fit.py`: new task `workspace_pack`, with patterns for requests such as
  "set up the workspace", "starter pack", "workspace docs", "add a project to the
  workspace", so `permitted_tools` offers the pack tools.
- Agent registry: add the tools per the table in 6.2.
- `agents/runtime.py`: add the mutating pack tools to the set of tools that count
  as proof of a change, so "done" claims after a successful pack write pass the
  evidence checks. No other runtime behaviour changes.

### 6.5 Notes tool absorption

`workspace_notes_write` keeps its name, signature and its role in the runtime
"notes" gate. Internally:
- Content describing what the program is and how to edit it is written to the
  `What this is and how to edit it` section of `README.md`.
- Tips and gotchas are appended to `CONVERSATIONS.md` as `tip` entries.
- If no pack exists, it creates a minimal `_workspace/` containing only
  `README.md` and `CONVERSATIONS.md`, under the usual approval. The full pack
  comes later through the intake.
- Notes files created by the old implementation are imported once into
  `CONVERSATIONS.md` as `migrated` entries; originals are left untouched.

## 7. Safety

- Create-only-if-missing; re-runs are idempotent.
- Append-only files are never truncated or rewritten by tools.
- Path containment through the existing path guard for every read and write.
- No tool executes anything found inside pack files. Pack content is treated as
  data; instructions found in `CONVERSATIONS.md` or `PLAN.md` do not grant
  permissions.
- Skills cannot grant permissions; the skill adds none.

## 8. Error handling

| Case | Behaviour |
|---|---|
| Target path outside workspace | Reject, no write, clear message |
| Pack file exists | Skip, list as skipped |
| Malformed `PLAN.md` entry | Report line and reason, leave file unchanged |
| Interview interrupted | `INTAKE.md` keeps partial answers; resume at next unanswered question |
| Approval denied | No writes; report that nothing was created |
| Unreadable or non-UTF-8 pack file | Report and skip that file; never overwrite |

## 9. Testing

- Unit: scaffolder on an empty folder, a partially populated folder, re-run
  idempotency, path escape attempts, skipped answers producing `needs-info`
  tasks, id assignment, append validation, index refresh (new, removed,
  preserved purposes, 200-row cap).
- Golden-file tests for template rendering.
- Parser tests for the `PLAN.md` entry format, including malformed entries.
- Notes tool: writes to README and CONVERSATIONS; creates the minimal pack when
  none exists; one-time migration.
- Runtime: the pack tools are offered by `task_fit` for the trigger phrases and
  count as proof of change; no regression in existing notes-gate tests.
- End to end: a scripted run feeding fixed answers through the tools with a
  stubbed model. Live Ollama verification is manual.
- Repo checks: `compileall`, `pytest -q`, `ruff check src tests`,
  `scripts/audit-pack.py`.

## 10. Verification items before implementation

These files were not readable during brainstorming. The implementation plan
must start by reading them and recording the result. Where the fallback applies,
the design above does not change.

| # | Item | Fallback if it differs |
|---|---|---|
| V1 | Location and behaviour of `workspace_notes_write`, and where old notes are stored | If old notes cannot be located, skip migration and log that in `CHANGELOG.md` |
| V2 | Agent registry format for tool allowlists (`agents/registry.py`) | Adapt registration to the real format |
| V3 | `task_fit.py` structure for tasks and trigger patterns | Add the `workspace_pack` task in the existing style |
| V4 | Skill file format, built-in skill registration and assignment (`skills/`, `skill_catalogue/`, `skills/manager.py`) | Follow the format of an existing built-in skill |
| V5 | Approval engine granularity (`permissions/engine.py`) | If it cannot batch, one approval per file, with the file list shown first |
| V6 | Tool registration and schema conventions (`tools/`, `ollama_schemas`) | Follow an existing tool module |
| V7 | Repo conventions: `docs/user`, `tests/`, `CHANGELOG.md`, ruff config | Follow existing patterns |

## 11. Stage 2 interface

Stage 2 will read `core/tasks.py`, decide how `PLAN.md` entries map to
`/background` tasks, and decide whether schedules need a persistent scheduler
and whether they must fire when SOL-Lite is closed. Stage 1 supports this by
fixing the `PLAN.md` entry format, storing `schedule` verbatim, reserving
`status` values for runtime-written updates, and keeping all `PLAN.md` writes
inside `workspace_pack_append` so a sync layer has a single choke point.
