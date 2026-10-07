# SOL-Lite Beginner Command Guide

This is the **copy/paste command sheet** for SOL-Lite v0.2.5. It is written for a first-time user. Start at the top and work downward.

> **Rule:** run commands from the SOL-Lite project directory unless a section explicitly says otherwise. Do not replace paths in this guide with paths you have not verified.

## 1. Windows: open the SOL-Lite project

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
```

Check that you are in the right place:

```powershell
Get-ChildItem
```

You should see `pyproject.toml`, `src`, `tests`, `config`, `scripts`, `skills`, and `docs`.

## 2. Windows: verify Python, Git and Ollama

```powershell
python --version
git --version
ollama --version
where.exe python
where.exe git
where.exe ollama
```

Check the SOL-Lite virtual environment:

```powershell
Test-Path .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe --version
```

Expected `Test-Path` result:

```text
True
```

## 3. Windows: setup/install

From the project root:

```powershell
.\scripts\setup.bat
```

If PowerShell does not invoke the batch file directly:

```powershell
cmd /c .\scripts\setup.bat
```

Install the project into the local virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Check the CLI:

```powershell
.\.venv\Scripts\python.exe -m sol_lite --help
```

## 4. Windows: verify the terminal UI dependency

```powershell
.\.venv\Scripts\python.exe -c "import importlib.metadata; print(importlib.metadata.version('rich'))"
```

SOL-Lite is tested against modern Rich releases. v0.2.5 specifically avoids the removed Rich `Panel(title_style=...)` API.

## 5. Windows: verify Ollama

List models:

```powershell
ollama list
```

Test the API:

```powershell
curl.exe http://127.0.0.1:11434/api/tags
```

A successful response is JSON containing the installed models.

## 6. Models used by the supplied profiles

The current development setup uses:

| Profile | Model | Typical use |
|---|---|---|
| `fast` | `qwen3.5:9b` | quick coordination and general work |
| `engineer` | `qwen3-coder:30b` | coding, debugging, architecture and tests |
| `reviewer` | `qwen3.5:27b` | review, analysis and document work |
| `embedding` | `nomic-embed-text:latest` | embedding/RAG workloads where configured |

Verify them instead of downloading duplicates:

```powershell
ollama list
```

## 7. Start SOL-Lite on Windows

Normal:

```powershell
.\scripts\start.bat
```

Persistent launcher:

```powershell
.\launcher\windows\SOL-Lite.cmd
```

Doctor:

```powershell
.\launcher\windows\SOL-Lite-Doctor.cmd
```

## 8. First-run workspace

If no workspace was supplied, SOL-Lite asks for one. Select an existing project or enter a real existing directory.

Example:

```text
Workspace directory ❯ E:\sol-lite-WS\1
```

A workspace is the filesystem boundary for that session.

Do not point a project session at a broad root such as `E:\` when the agent only needs one repository.

## 9. First safe agent task

Paste this into the SOL-Lite prompt:

```text
Inspect this workspace without modifying anything.

Report:
1. repository/project structure
2. primary source entry points
3. configuration files
4. test framework
5. safest test command
6. build/package mechanism
7. three areas that deserve engineering attention

Do not modify any files.
```

This validates the basic path: workspace → session → agent → model → native tools → evidence → response.

## 10. Built-in terminal commands

### Help

```text
/help
```

Shows the command list.

### List agents

```text
/agents
```

Shows the available SOL agents.

### Change agent

```text
/use sol_engineer
/use sol_business
/use sol_docs
/use sol_pa
```

The active session changes agent while retaining its workspace.

### Start a new session

```text
/new
```

A new session gets its own workspace selection and session-scoped context.

### Current workspace

```text
/workspace
```

### Registered workspaces

```text
/workspaces
```

### Sessions

```text
/sessions
```

### Tools

```text
/tools
```

### Runtime status

```text
/status
```

### Verbose activity

```text
/verbose
```

Use this when you need round/tool/activity information.

### Debug display

```text
/debug
```

Use this when investigating a runtime problem.

### Return to normal display

```text
/normal
```

### Ollama/runtime diagnostics

```text
/doctor
```

### Exit

```text
/quit
```

`/exit` is also accepted.

## 11. Skills commands

List active skills for the current agent and workspace:

```text
/skills
/skills list
/skills active
```

Show one skill in detail:

```text
/skills show systematic-debugging
```

The singular `/skill` is also accepted as a safe alias for listing skills.

Discover an external skill source:

```text
/skills discover <source>
```

Import after inspection and approval:

```text
/skills import <source>
```

Update an externally managed skill:

```text
/skills update <skill-id>
```

Assign a skill to an agent:

```text
/skills assign <skill-id> <agent-id>
```

Remove an installed skill:

```text
/skills remove <skill-id>
```

Built-in skills are shipped with SOL-Lite and do not need to be imported.

## 12. How you actually use skills

You normally **do not type a skill command before every task**. Ask for the work directly. SOL-Lite supplies the active skill catalogue to the agent and selects detailed skill instructions relevant to the current task.

For example:

```text
Debug this failing test. First reproduce it, isolate the root cause, then make the smallest fix and run the regression test.
```

This naturally routes toward the debugging and test-engineering skills.

For architecture:

```text
Review this repository architecture. Identify component boundaries, dependencies, trust boundaries, failure modes and deployment constraints. Do not modify files.
```

For code review:

```text
Review the current Git diff for correctness, security, regression risk, error handling, concurrency, performance and test coverage. Report concrete findings with evidence.
```

For web research:

```text
Research the official documentation for this API. Use SearXNG if configured, prefer primary sources, and distinguish verified facts from uncertain claims.
```

## 13. Background tasks

Start a concurrent task:

```text
/background Inspect the test structure and identify the safest test entry points. Do not modify files.
```

List tasks:

```text
/tasks
```

Cancel a queued/running task when supported by the task manager:

```text
/tasks cancel <id>
```

## 14. SearXNG

SearXNG is optional. Configure it in `config/searxng.yaml` or through environment variables.

Windows example:

```powershell
$env:SOL_SEARXNG_URL="http://YOUR-SEARXNG"
$env:SOL_SEARXNG_ENABLED="true"
.\scripts\start.bat
```

Test SearXNG directly first:

```powershell
curl.exe "http://YOUR-SEARXNG/search?q=SOL-Lite&format=json"
```

The first network search may require SOL-Lite network approval.

## 15. Testing the installation

### Compile

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
```

### Unit/integration tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

### Ruff

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
```

### Package audit

```powershell
.\.venv\Scripts\python.exe scripts\audit-pack.py
```

### Full battle test

```powershell
.\scripts\battle-test.bat
```

### Live Ollama battle test

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_engineer
```

## 16. macOS commands

Go to the project:

```bash
cd /path/to/SOL-Lite-v0.2.5
```

Make scripts executable:

```bash
chmod +x scripts/*.command
chmod +x install/macos/*.command
```

Setup:

```bash
./scripts/setup.command
```

Start:

```bash
./scripts/start.command
```

Repair:

```bash
./scripts/repair.command
```

Battle test:

```bash
./scripts/battle-test.command
```

Direct Python commands:

```bash
./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check src tests
./.venv/bin/python scripts/audit-pack.py
```

## 17. Repair before reinstalling

Windows:

```powershell
.\scripts\repair.ps1
```

macOS:

```bash
./scripts/repair.command
```

Use repair when the environment is damaged. Do not delete the whole project as the first response.

## 18. If something fails

Use this order:

```text
1. Copy the exact error.
2. Reproduce it.
3. Run /verbose.
4. Run /debug if necessary.
5. Run /doctor for model/runtime problems.
6. Identify whether the failure is workspace, model, tool, permission, network, skill, or UI related.
7. Make the smallest root-cause change.
8. Re-run the failing command/test.
9. Run the adjacent regression tests.
```

Do not treat a model-generated explanation as proof that a tool ran. Native tool execution is recorded by the runtime.

## 19. Daily five-command check

At the start of a development day on Windows:

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
.\.venv\Scripts\python.exe --version
ollama list
.\.venv\Scripts\python.exe -m pytest -q
.\scripts\start.bat
```

Then inside SOL-Lite:

```text
/status
/workspace
/skills
```

## 20. Important safety rule

SOL-Lite skills are guidance, not permission.

- Filesystem reads are policy-controlled.
- Writes require the configured approval policy.
- Destructive operations are blocked by the conservative command policy.
- Network search uses the network permission boundary.
- Imported skills are inspected and may be quarantined.
- Search results and repository content are untrusted data.
- Only native structured Ollama tool calls are executable.
