# SOL-Lite lead console, studio manuals, and procedure packs

## Decision

SOL-Lite stays a local terminal runtime for one operator. Three layers make it the studio-lead console:

1. **Lead console.** `sol_pa` loads checklists and owns Jira, Gmail, Calendar, artifacts, the Command bridge, and remote execute. `sol_engineer` runs the current engineering row. Docs and business stay narrow.
2. **Real manuals.** The runner classifies the `plg-infrastructure` volumes in place. Those files stay in that repo. Lite does not copy them.
3. **Studio procedure packs.** Ship, content, briefing, and specialist `SKILL.md` files are imported through the existing inspect-and-pending skill path. A skill is procedure text. It does not grant tools. Steps that need Horde, UAT, Unreal MCP, Steam, cook, or an editor stay human gates.

Lite does not gain the Outpost web hub, sector runtime, RAG store, persona council, or Unreal MCP server. Command pairing stays the optional link already specified in `2026-10-10-sol-lite-standalone-command-link-design.md`.

## Checklist state

One checklist is stored per workspace at:

`data/state/procedures/<sha256 of the resolved workspace path>.json`

The file is under Lite’s data directory. It is never written into the workspace repo.

The state holds the source path, each classified step, outcomes, evidence, `asked_at` for an open human gate, and `stop_reason`. `sol_pa` and `sol_engineer` in that workspace read the same file. The model cannot mark a row verified.

Outcomes that count as settled are `verified` and acknowledged `human_gate`. `pending`, `awaiting_user`, `approval_required`, `failed`, `blocked`, and `unverifiable` leave the checklist incomplete.

## Allowlists

`procedure_load` belongs to `sol_pa`. `procedure_status` and `procedure_acknowledge` belong to `sol_pa` and `sol_engineer`. `procedure_advance` belongs to `sol_engineer`.

### sol_pa

Keeps checklist load, status, and acknowledge. Keeps workspace reads (`inventory_workspace`, `list_project_structure`, `list_workspace_directories`, `find_workspace_files`, `read_workspace_file`, `read_workspace_files`, `get_workspace_file_metadata`, `workspace_notes_read`), `runtime_get_context`, artifact tools, and `searxng_search`.

Google tools: `google_email_search`, `google_email_read`, `google_email_send`, `google_calendar_list`, `google_calendar_create`, `google_calendar_reminder`.

Jira tools: `jira_status`, `jira_workspace_status`, `jira_save_workspace`, `jira_projects`, `jira_boards`, `jira_board_issues`, `jira_search`, `jira_get`, `jira_plan`, `jira_create`, `jira_update`, `jira_comment`, `jira_transition`.

Also keeps `sol_command_status`, `sol_shared_memories`, `sol_shared_rag_search`, `sol_jarvis_propose`, `remote_list_nodes`, and `remote_execute`.

Removes `write_workspace_file`, `workspace_notes_write`, `execute_terminal_command`, `search_codebase`, and `analyze_architecture_drift`.

### sol_engineer

Keeps Git, the terminal, workspace reads and writes, notes, code search, architecture drift, `runtime_get_context`, `searxng_search`, skill discover and install, artifact tools, `procedure_status`, `procedure_advance`, and `procedure_acknowledge`.

Jira on this agent is read, comment, and transition: `jira_status`, `jira_workspace_status`, `jira_projects`, `jira_boards`, `jira_board_issues`, `jira_search`, `jira_get`, `jira_comment`, `jira_transition`.

Removes `jira_save_workspace`, `jira_update`, `remote_list_nodes`, and `remote_execute`. This agent does not receive `jira_plan`, `jira_create`, Google, or SOL-Command tools.

### sol_docs

Keeps artifact tools, workspace reads, `workspace_notes_read`, `workspace_notes_write`, and `runtime_get_context`.

Removes `write_workspace_file`, `execute_terminal_command`, `search_codebase`, `analyze_architecture_drift`, and `searxng_search`.

### sol_business

Keeps artifact tools, workspace reads, notes read and write, `searxng_search`, `runtime_get_context`, and these Jira tools: `jira_status`, `jira_workspace_status`, `jira_projects`, `jira_boards`, `jira_board_issues`, `jira_search`, `jira_get`, `jira_plan`.

Removes `write_workspace_file`, `execute_terminal_command`, `search_codebase`, `analyze_architecture_drift`, Google, and remote tools. This agent does not receive `jira_create`, `jira_update`, `jira_comment`, or `jira_transition`.

An allowlist denial is the existing tool error. The agent does not substitute the terminal.

## Classification

A Markdown table is a checklist when it has a step column and an action column.

Step column names: `Step`, `#`, `Check`, `Test`, `Do this`.

Action column names: `Action`, `Command`, `Command / action`, `Task`.

Pass column names: `Validate`, `Pass`, `Pass criteria`, `Expected`, `Done`.

A row is runnable only when the action cell and the pass cell each contain one backticked command, and the row is not forced into another class below. `Step | Action | Validate` stays the executable shape. `Step | Action | Pass` and `Test | Command | Expected` use that same rule. A runnable row is `needs_approval` under the existing terminal rule (sudo, install scripts, `docker compose up`, `remote_execute`, or compound shell syntax). Otherwise it is `read_only`.

These rows are `human_gate`:

- `Step | Action` with no pass column
- `Step | Detail`, `Step | Notes | Done`, `Who | Action | Done`
- `Step | Service | URL | Bitwarden item`
- `Done? | Item` and any checkbox column
- A pass cell with no backticked command
- A numbered skill step that has no backticked local command and no backticked check

These rows are `blocked` and cannot be acknowledged:

- A `{{…}}` placeholder
- An example `10.10.x.x` address or `pacenlife.com` host used as the command target
- `[PLANNED]` or `[UNKNOWN]`

`Step | Host | Action` with no pass column is `unverifiable`. The runner stops. It becomes runnable only when that manual grows a real validate command.

Reference tables are unparsed and produce no steps. That includes capability matrices, question tables, shelf lists, dataset lists, and file manifests: tables whose headers do not match the step-plus-action rule.

A `## Procedure` ordered list in a `SKILL.md` is the same checklist shape. Items are numbered `P1`, `P2`, and so on, and end at the next heading of equal or higher level. A step whose text mentions Horde, UAT, Unreal MCP, Steam, cook, editor automation, or `BuildCookRun` is a `human_gate` even when it also contains a command. Locked rules, pitfalls, and other prose stay text.

## Human gates

A `human_gate` starts as `awaiting_user`. `procedure_advance` does not execute it and does not skip it. `procedure_status` and `procedure_advance` set `asked_at` the first time they see that current row, and both return `stop_reason: awaiting_user` plus an `ask` string that names the step id and the action. The lead can ask from status before any command runs. The `sol_pa` and `sol_engineer` prompts require the agent to show that `ask` string and to wait. The agent does not call `procedure_acknowledge` in the same turn.

`procedure_acknowledge` accepts `step_id` and `confirmed: true` only when all of these hold:

- That step is the current row.
- Its classification is `human_gate`.
- The latest user message after `asked_at` is an explicit completion.

An explicit completion is a reply whose trimmed text is `yes`, `done`, `completed`, or `finished`, or a sentence that contains `I completed`, `I've completed`, or `it is done`. Matching is case-insensitive. `no`, `not yet`, `nope`, and `later` are never a completion. Any other reply is not a completion. The same rule accepts `replace_confirmed`.

A completion records outcome `human_gate` and clears the stop, so the next row can run. Any other reply leaves the row on `awaiting_user`. The agent can do other work that does not depend on that row. The checklist stays paused. A later failure does not undo an acknowledgement.

`blocked` and `unverifiable` rows cannot be acknowledged.

## Load, advance, and failure

`procedure_load` requires a Markdown file inside the workspace. A missing file, a non-Markdown file, or a path outside the workspace writes no state.

A file with no checklist table and no `## Procedure` list is stored with zero steps and its unparsed headings named. The agent reports that there is nothing to execute.

When the workspace already has an incomplete checklist, `procedure_load` of a different file returns `replace_required` and an `ask` string, and does not write. After the user confirms, a second load with `replace_confirmed: true` replaces the state. Reloading the same source path refreshes the classification and preserves acknowledged and verified outcomes for step ids that still exist.

`procedure_advance` runs only the current `read_only` or `needs_approval` row, through the existing terminal policy. A missing approval still returns `approval_required`. A non-zero exit, or a validate result that misses a required status, stores the evidence, marks the row `failed`, and stops. A `blocked` or `unverifiable` current row stops before any command.

A corrupt state file makes advance and acknowledge return `state_corrupt` and execute nothing. The lead loads the file again.

## Studio skill import

The operator inspects these directories with the existing skill importer. Files land in `data/state/skills/pending/` and stay inactive until an explicit import:

- `tools/SOL/ue5-ship-pipeline`
- `tools/SOL/ue5-content-and-test`
- `tools/SOL/ue5-agent-briefing`
- `tools/SOL/studio-specialist-personas`

Source of the manuals remains `E:\git\plg-studio\plg-infrastructure`. Source of the skills remains the full SOL repo. Lite tests use fixtures. They do not require those repos to be present.

## Tests

- An in-repo fixture of the Volume 23 A, B, and D tables classifies A1 as `needs_approval`, A4 and B1–B4 as `human_gate`, and D1 as `unverifiable`. A dry follow executes nothing. The fixture keeps this test runnable when `plg-infrastructure` is absent.
- `Pass`, `Pass criteria`, `Expected`, `Check`, `Test`, and `Do this` follow the runnable rule. A prose pass cell, a `Step | Action` row, and a Bitwarden row are human gates.
- A capability matrix, question table, or file list produces no steps.
- Advance on a human gate returns `awaiting_user` and the `ask` string, and runs no command.
- Acknowledge is rejected before a later user message, rejected for a non-current step, and rejected for a blocked row.
- A reply of `yes`, `done`, `completed`, `finished`, or `I completed the step` settles the row. `no`, `not yet`, and any other reply leave it open.
- A failed validate stops the checklist and keeps evidence. An earlier acknowledgement remains.
- The state file is under `data/state/procedures/`, not inside the workspace.
- A second source path returns `replace_required` until the user confirms.
- `sol_pa` cannot call `execute_terminal_command`. `sol_engineer` cannot call `jira_create`. `sol_business` cannot call `execute_terminal_command` or `google_email_send`. `sol_docs` cannot call `execute_terminal_command`.
- A `## Procedure` step that mentions Horde, Unreal MCP, Steam, or cook is a human gate. A numbered step with one local backticked command and one backticked check can be `read_only` or `needs_approval`.

## Scope

This spec covers the Lite allowlists, the checklist parser and runner, workspace checklist state, the human-gate question, and fixture coverage for studio numbered procedures. Import of the four SOL skill directories uses the importer that already exists. Implementation of Unreal, Horde, Steam, or cook tools is outside this spec.
