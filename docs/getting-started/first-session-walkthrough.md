# First session: from launch to a useful handoff

This is a human-operated walkthrough, not a record of tests already run. Finish [setup](full-setup-first-run.md) first; enable desired extras through [full feature configuration](full-feature-configuration.md). Windows commands below run in PowerShell from the repository folder. On macOS use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`.

## 1. Create a practice workspace

Use a separate folder to avoid practising on the installation source. These commands deliberately create practice files when you run them:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SOL-Lite-Practice\notes"
Set-Content -Path "$env:USERPROFILE\SOL-Lite-Practice\notes\brief.md" -Value 'Goal: prepare a small project plan. Owner and deadline are not yet decided.'
.\.venv\Scripts\python.exe -m sol_lite start --agent sol_pa --workspace "$env:USERPROFILE\SOL-Lite-Practice"
```

On macOS create `~/SOL-Lite-Practice/notes` in Finder, create the UTF-8 file `notes/brief.md` with the text above, then start with `--workspace "$HOME/SOL-Lite-Practice"`.

## 2. Confirm context and limits

Type each slash command separately:

```text
/workspace
/agents
/skills list
```

The workspace must be the practice folder. Four standard agents should be listed. If it differs, correct the selection before continuing.

Then paste this as one message:

```text
This is my first session. Use read-only tools to inspect the selected workspace and notes/brief.md. Report the actual workspace, active agent, source facts and unknowns. Do not run terminal commands, modify files, contact external services or invent an owner/deadline. Distinguish tool evidence from assumptions.
```

Expected evidence: the actual file content and an accurate report of the missing owner/deadline. A polished answer without file evidence is not a pass.

## 3. Try each specialist in the same workspace

Switch, then paste the corresponding message. Changing agents is not a file-based handoff by itself.

```text
/use sol_business
```

```text
Read notes/brief.md and draft a short project plan in your reply. Include decisions needed, risks and next actions. Do not invent a budget, owner or deadline. Do not write files, run commands or use network tools.
```

```text
/use sol_docs
```

```text
Read notes/brief.md. Draft a clear one-page brief in your reply with confirmed facts and a separate missing-information list. Do not generate artifacts, write files or contact services yet.
```

```text
/use sol_engineer
```

```text
Inspect this workspace using file tools only. Report whether it contains an application or tests. If none exist, say so; do not invent a runtime, test result or implementation task. Do not execute commands or edit files.
```

Each specialist must actually respond using its configured model. Record model-load failures separately from tool or permission failures. Return with `/use sol_pa`.

## 4. Make one deliberate output

This request authorizes a single write. Role-path writes may not show an approval popup:

```text
Read notes/brief.md. Create only plans/first-session.md with the confirmed goal, undecided owner/deadline, and three proposed next steps clearly labelled as proposals. Do not modify the input, run commands or contact services. After writing, read the file back and report its actual path.
```

Open the file in your editor and compare it with the brief. If an approval appears, inspect the exact target and arguments before deciding. Decline unrelated actions.

## 5. Try one background read

```text
/background Read notes/brief.md and plans/first-session.md. Report contradictions or invented facts. Do not change files, run commands or use external services.
/tasks
```

Check `/tasks` again when appropriate. Completed is different from queued/running. A cancellation request does not undo any already completed operation. Skip this exercise if the task manager reports unavailable.

## 6. Prove desired integrations separately

Use the [integration starter prompts](../user/starter-prompt-packs.md#integration-check-pack) only after configuring the corresponding service. One narrow approved read is enough for an initial connection check. Sending email, creating meetings, modifying Jira, pushing Git and executing remote writes are separate operations; they are not required to prove a first session.

For artifacts, first check dependencies, then request one sample in a new filename and inspect its rendered preview. For voice, use a harmless sentence and verify both recognition and playback.

## 7. Save a handoff and close

```text
Read the practice files and create only notes/session-handoff.md. Record what actually completed, output paths, open decisions, failed or untested features and the next suggested action. Do not include credentials, claim an integration was tested without a tool result, or change any other file. Read the handoff back after saving.
```

Check `/tasks`, open the handoff and type `/quit`. Sessions are in memory and recent context is capped at six turn pairs. The file is your durable handoff.

On the next launch, select the same folder and paste:

```text
Read notes/session-handoff.md and the files it references. Summarise the last confirmed state and ask for the missing decision needed to continue. Do not repeat completed operations or change files yet.
```

## First-session completion record

Copy this into your own notes and fill it with actual observations:

```text
Application version / Git commit:
Workspace:
PA read-only request: passed / blocked + reason
Business read-only request: passed / blocked + reason
Docs read-only request: passed / blocked + reason
Engineer read-only request: passed / blocked + reason
Single output file inspected:
Background task result or not attempted:
Integration reads actually checked:
Voice / artifact checks actually performed:
Untested features:
Handoff file:
Next decision:
```

Continue with [starter prompt packs](../user/starter-prompt-packs.md) for real tasks.
