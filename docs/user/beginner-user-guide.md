# SOL-Lite: complete beginner user guide

For the v0.2.6 tree, checked by reading source without running the application. Start with [setup](../getting-started/full-setup-first-run.md). The [system guide](../architecture/beginner-system-guide.md) explains files, connections and persistence.

Use [full feature configuration](../getting-started/full-feature-configuration.md) to update agents and connect services, the [first-session walkthrough](../getting-started/first-session-walkthrough.md) for practice, and [starter prompt packs](starter-prompt-packs.md) for copy-and-paste tasks.

## 1. Put commands in the right window

PowerShell or macOS Terminal starts the application. From the repository folder, a Windows shell command looks like:

```powershell
.\.venv\Scripts\python.exe -m sol_lite doctor
```

The macOS prefix is `.venv/bin/python -m sol_lite`. Use that prefix for shell subcommands mentioned later, such as `jira-connect`. They are not slash commands.

Once the SOL-Lite banner appears, type normal sentences or slash commands such as `/help`. Do not paste setup commands into chat expecting them to become terminal input. Ask for a tool operation when that is your intent.

Enter sends a message. The banner describes Shift+Enter for a newline; support depends on the terminal. `/quit` or `/exit` exits.

## 2. Choose the working folder

A workspace is the folder containing the files for this task. It need not be the SOL-Lite installation folder. Confirm the target before work:

```text
/workspace
```

- `/workspaces` lists remembered folders.
- `/workspace new` opens the workspace picker.
- `/workspace 1` opens the first recent folder.
- `/workspace C:\Users\YourName\Documents\MyProject` selects an existing folder; replace the example with yours.
- `/new` starts a fresh session and asks for a workspace.
- `/sessions` lists sessions in this running application; it does not restore yesterday's chat.

For Git folders, the shell may offer the repository root and ask whether to trust its remotes. Trusting a checkout can skip repeated remote approvals; it does not authorize every mutation.

Local file tools enforce workspace boundaries. Separately configured integrations may access other named resources. Check those targets too. A workspace boundary does not determine whether a configured network model provider receives your messages.

## 3. Pick an agent

```text
/agents
/use sol_pa
```

- **SOL PA (`sol_pa`)** coordinates, plans and uses supported personal integrations. Default profile `fast`, model `qwen3.5:9b`.
- **SOL Business (`sol_business`)** analyses business material and writes plans and reports. Default profile `reviewer`, model `qwen3.5:27b`.
- **SOL Docs (`sol_docs`)** handles documents, extraction and artifact creation. Default profile `reviewer`, model `qwen3.5:27b`.
- **SOL Engineer (`sol_engineer`)** handles source analysis, debugging, Git and technical work. Default profile `engineer`, model `qwen3-coder:30b`.

Settings can override these defaults. Agent names describe roles, not guaranteed accuracy. Studio Admin is separately gated and normally hidden.

## 4. Describe a clear task

Name the input, requested output, allowed operations and finish condition. For inspection:

```text
Read this workspace. Explain what the project does and name the files supporting each conclusion. Do not run commands or change files. Say what you could not verify.
```

For a document:

```text
Read notes/meeting.md. Create docs/meeting-summary.md with decisions, owners and next steps. Do not invent dates or owners. Flag missing information. Change only that output file.
```

For code:

```text
Inspect this reported error and relevant source. Explain the likely cause and propose a small fix. Do not edit files or run tests yet.
```

Read actual tool results and open the output files. An agent's statement that a file exists or a test passed is not sufficient evidence. A failed tool operation remains incomplete.

## 5. Understand approval prompts

Read the operation, target and arguments before approving:

- `y` approves that exact operation once.
- `s`, where offered, grants the applicable scope for the rest of the session. It is broader than one operation.
- Use the prompt's deny choice for an unexpected action.

**Not every write produces a popup.** With filesystem writes enabled, role-path writes may run directly. All four standard agents have roots such as `docs/`, `notes/` and `plans/`; Engineer also has `src/`, `tests/`, `scripts/` and `config/`. Out-of-role file paths require the file approval gate. See [approvals](approvals.md).

Local reads normally need no popup. Network access, private-account reads and integration writes have separate permissions. Destructive and nested-shell commands remain blocked even with approval. Keep Git history or backups before requesting edits. Skills do not grant permission.

## 6. Check progress and diagnose a failure

```text
/status
/tools
/verbose
/debug
/normal
/doctor
```

`/tools` shows the active runtime tool surface. Verbose/debug display more activity; `/normal` restores compact display. Chat `/doctor` reports model and integration diagnostics; the shell `doctor` subcommand also checks local runtime health.

Record the error, workspace, selected agent and model. Ask for a read-only explanation before repeating a failed write. Reinstalling does not solve a permissions denial or unavailable external service.

## 7. Use and manage skills

Skills are reviewed instruction packages, not installed programs or account connections. Normally describe the task and let relevant guidance be selected.

```text
/skills list
/skills show systematic-debugging
```

To inspect and import an external package, replace the example path:

```text
/skills discover C:\path\to\skill-folder
/skills import C:\path\to\skill-folder
```

Import asks about installation and permission. Warnings can quarantine a skill instead of activating it. Imports are assigned to the active agent. Sources include folders, a `SKILL.md`, ZIP archives and GitHub sources; network sources need network permission.

Use the real ID from the list for maintenance:

```text
/skills update skill-id
/skills assign skill-id sol_engineer
/skills remove skill-id
```

Read the [full catalogue](skills-full-catalog.md) for shipped skills and examples. A skill cannot prove that a task succeeded.

## 8. Background tasks

```text
/background Inspect documentation for broken references. Do not edit files or run commands.
/tasks
```

A background task has an independent session. The default task-manager worker limit is four. States include queued, running, cancelling, completed, failed and cancelled.

```text
/tasks cancel TASK_ID
```

Replace `TASK_ID` with the displayed ID. Queued tasks can stop before starting; running cancellation is cooperative and may wait for the runtime to return. It does not undo completed operations. These tasks are process-local work, not a persistent scheduler or overnight monitor.

## 9. Settings and voice

`/settings` opens user preferences. Settings live outside the checkout; permission policy is separate. Restart after editing configuration files directly so bootstrap reloads them.

```text
/listen
/speak
```

`/listen` records speech and sends recognised text as a message. `/speak` toggles spoken replies. Run the shell subcommand `voice-status` to check readiness. Missing microphone permission, eSpeak-NG, packages or voice weights can prevent voice while text chat works. Preferences live in `data/state/voice.json`. Hosted voice providers need their configured endpoint credentials.

`/flare on` and `/flare off` control character manner for this sitting. It starts off, survives `/new`, and ends on quit. It does not change permission policy.

## 10. Documents, presentations, spreadsheets and diagrams

The standard installer does not include artifact extras. When you want artifact tools, install their packages in the app environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[artifacts]"
```

Office-file PDF exports additionally need LibreOffice. Mermaid image exports need Node.js and Mermaid CLI. Follow [artifact setup](artifacts.md) before requesting those exports. Microsoft Office is not required.

Ask the agent to check `artifact_dependencies`, create the artifact, validate it and render it where supported. Use a new filename for revisions: the artifact pipeline does not overwrite existing outputs. Open the artifact and inspect it before sharing. Writing spreadsheet formulas does not prove that calculated results were produced.

## 11. Optional services and specialist workflows

None of these is needed for local chat. Follow the linked setup before asking for the feature:

- **SearXNG search:** supply an actual private server with JSON search enabled. The shipped private address is an example; search is disabled by default. [Search setup](../integrations/searxng.md).
- **Google Gmail/Calendar:** install `.[google]`, enable the required Google APIs, obtain a Desktop OAuth client JSON, then run `google-connect --client-secrets` with its path. `google-status` checks saved authorization, not a successful API call. No background inbox monitor is supplied. [Google guide](../integrations/google-workspace.md).
- **Jira Cloud:** run `jira-connect` and answer site, account, token and granted-project prompts. `jira-status` probes the server. PA and Engineer have project-scoped tools. [Jira guide](../integrations/jira.md).
- **SOL-Command:** an administrator supplies an invite and approves the Lite instance. The PA receives assigned-sector tools. Skill sync stages packs for review; it does not activate them. Jarvis submissions remain pending. [Beginner pairing runbook](dummies-command-link.md).
- **Studio Odoo:** bind the required studio checkout and prepare source files. The PA builds CSV import packs for manual review/import; it does not operate Odoo or file tax returns. [Beginner Odoo guide](dummies-studio-odoo.md).
- **Remote hosts/procedures:** hosts must be explicitly configured, with distinct lab/production restrictions. `/follow workspace-relative-manual.md` performs a dry inspection; a checklist does not authorize execution. [Studio change guide](studio-change.md).
- **Portable administrator tool belt:** a separate owner-only USB workflow with additional gates. [Full administrator setup](admin-toolbelt-full-setup.md) and [first-day guide](dummies-admin-stick-m2.md).
- **MCP:** an advanced integration surface, not a chat prerequisite. Consult [MCP development documentation](../development/mcp.md) alongside the manifest; the current manifest does not declare an `mcp` extra.

Use `/help` for chat commands and the shell command `python -m sol_lite --help` through your app interpreter for subcommands. The [CLI reference](cli-reference.md) lists integration commands.

## 12. Preserve work before quitting

Save important findings as workspace files. Workspace registration persists, but sessions are held in memory and recent conversation context retains only six user/assistant turn pairs. `/sessions` is not a complete archived chat browser.

Check `/tasks`, review your outputs and type `/quit`. Back up actual workspace folders, repository configuration, required `data/` state and user settings. Credentials are stored in the OS keyring: copying a repository does not transfer account access. Reconnect on a new machine. Keep private data and `.env` out of public backups.

To move machines, clone and install there rather than copying `.venv`. For repairs and upgrades, use the [repair](../getting-started/repairing.md) and [upgrade](../getting-started/upgrading.md) guides after preserving work.
