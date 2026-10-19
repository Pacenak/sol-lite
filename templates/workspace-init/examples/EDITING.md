# Worked setup and editing examples

All names, dates and outcomes below are illustrative. They are not claims about
your current workspace. Apply them to copies, not to the template source kit.

## Initialize a Studio workspace

Copy the contents of `workspace/` to a new selected root. For example, replace:

```text
{{WORKSPACE_NAME}} -> Studio Sandbox
{{WORKSPACE_ROOT}} -> E:/sol-lite-WS/sandbox
{{WORKSPACE_ID}} -> unknown
{{PURPOSE}} -> Prototype tools and keep project planning in one place.
{{OWNER}} -> Pacer
{{DATE}} -> 2026-10-19
```

Keep `planning/SPRINT.template.md` as a reusable source with its sprint tokens.
Replace workspace-level tokens in copied documents. If SOL-Lite has created a
managed pack, the root CHANGELOG can instead contain:

```markdown
# Workspace changes
See the [authoritative shared log](_workspace/CHANGELOG.md).
```

Use that link only after checking the target exists.

## Add a project

Copy `project/` into `projects/harbour-demo/`. Replace project tokens with
`Harbour Demo`, `harbour-demo`, `Prototype a local document search workflow`,
`Python`, the real owner, and today's actual date. Keep `Status: planned` until
work starts. Then replace the empty registry statement in `docs/PROJECTS_INDEX.md`:

From `docs/`, use `../projects/` because both folders share the workspace root:

```markdown
- [Harbour Demo](../projects/harbour-demo/README.md): planned;
  prototype local document search; owner Pacer; reviewed 2026-10-19.
```

Verify the path exists before keeping it. Add actual project subfolders as the
work requires, then update the project INDEX rather than claiming the full
suggested structure already exists.

## Create and update a sprint

Copy `planning/SPRINT.template.md` to `planning/sprints/SPRINT-2026-01.md`,
creating `sprints/` if needed. Fill in:

```markdown
# Sprint 01 - Harbour Demo
Dates: 2026-10-19 to 2026-10-30
Owner: sol_pa
Status: planned

## Goal
Find one known document using the local search prototype.

## Work and acceptance
- [ ] sol_engineer: implement search; a known fixture returns the expected file.
- [ ] sol_docs: write a quick start; the owner can follow it on a clean setup.
```

Add this to `planning/INDEX.md` only after creating the file:

```markdown
- [Sprint 01](sprints/SPRINT-2026-01.md): Harbour Demo; owner sol_pa;
  planned; 2026-10-19 to 2026-10-30; reviewed 2026-10-19.
```

When work begins, update the sprint and inventory to `active`. Check tasks only
after acceptance checks pass. Record real test output in Review evidence.

## Record a change and hand it off

For a manual workspace, append an entry using the actual date and actor:

```markdown
### 2026-10-19 - sol_docs - Added first Harbour Demo sprint
- Changed: planning/sprints/SPRINT-2026-01.md and planning/INDEX.md.
- Reason: make the first implementation goal and acceptance checks explicit.
- Validation: confirmed both files exist and the inventory link resolves.
- Follow-up: sol_engineer to review feasibility; no implementation tests run.
```

For a managed pack, ask the acting agent to record the same facts through
`workspace_pack_append`; do not manually append to its managed log. Ask SOL PA
to refresh managed indexes if the new files cause drift.

## Example request to SOL PA

“Set up the workspace starter pack for Studio Sandbox. Use the optional
workspace-init templates for manual docs and planning files. Inspect existing
files first, merge rather than overwrite, and ask the remaining intake questions
one at a time. Use relative links, record only actual files, and log the result.”

## Before considering setup complete

- Check selected root, project names, owner, dates and actual workspace ID.
- Search instantiated documents for unresolved `{{` tokens; retained source
  templates may intentionally contain them.
- Open relative links and compare inventories with the real filesystem.
- Confirm there is one authoritative workspace change log.
- Remove sample facts and record unknowns without guessing.
- If using SOL-Lite, inspect `workspace_pack_status` for managed-pack issues.
