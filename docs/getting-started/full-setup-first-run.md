# SOL-Lite Full Setup and First Run

This is the canonical beginner setup for SOL-Lite v0.2.5 on **Windows and macOS**. It assumes no prior SOL-Lite knowledge.

## 1. What must exist before SOL-Lite can run

| Component | Required? | Purpose |
|---|---|---|
| Python 3.11+ | Yes | SOL-Lite runtime |
| Git | Recommended | Repository workflows and external skill sources |
| Ollama | Yes for agents | Local model provider |
| SearXNG | Optional | Private web research/search |

SOL-Lite creates a project-local Python virtual environment named `.venv`.

## 2. Windows: verify prerequisites

Open PowerShell:

```powershell
python --version
git --version
ollama --version
where.exe python
where.exe git
where.exe ollama
```

Then enter the project:

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
Get-ChildItem
```

The project root should contain `pyproject.toml`, `src`, `tests`, `config`, `scripts`, `skills` and `docs`.

## 3. Windows: install/setup

```powershell
.\scripts\setup.bat
```

If necessary:

```powershell
cmd /c .\scripts\setup.bat
```

Verify the local interpreter:

```powershell
Test-Path .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe --version
```

Install the project into that environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Verify the CLI:

```powershell
.\.venv\Scripts\python.exe -m sol_lite --help
```

## 4. Windows: verify Ollama

```powershell
ollama list
curl.exe http://127.0.0.1:11434/api/tags
```

The current development model set is:

```text
qwen3.5:9b
qwen3-coder:30b
qwen3.5:27b
nomic-embed-text:latest
```

Do not download duplicates if `ollama list` already shows the required model.

## 5. macOS: verify prerequisites

```bash
python3 --version
git --version
ollama --version
which python3
which git
which ollama
```

Enter the extracted project directory:

```bash
cd /path/to/SOL-Lite-v0.2.5
```

## 6. macOS: install/setup

Make the supplied scripts executable:

```bash
chmod +x scripts/*.command install/macos/*.command
```

Run setup:

```bash
./scripts/setup.command
```

Verify:

```bash
./.venv/bin/python --version
./.venv/bin/python -m sol_lite --help
```

## 7. Configure SearXNG only if you need web research

Edit:

```text
config/searxng.yaml
```

Set:

```yaml
searxng:
  url: "http://YOUR-SEARXNG"
  enabled: true
  timeout_seconds: 15
  max_results: 8
  categories: "general"
  language: "en"
  safesearch: 1
  engines: ""
```

Test the SearXNG API before blaming SOL-Lite:

Windows:

```powershell
curl.exe "http://YOUR-SEARXNG/search?q=SOL-Lite&format=json"
```

macOS:

```bash
curl "http://YOUR-SEARXNG/search?q=SOL-Lite&format=json"
```

If JSON is not enabled on the SearXNG server, enable the `json` search format in its settings.

## 8. Start SOL-Lite

Windows:

```powershell
.\scripts\start.bat
```

or:

```powershell
.\launcher\windows\SOL-Lite.cmd
```

macOS:

```bash
./scripts/start.command
```

The macOS application launcher is:

```text
launcher/macos/SOL-Lite.app
```

## 9. First-run workspace

When no workspace is supplied, SOL-Lite presents recent workspaces and a new-workspace option.

Select the project directory the agent should actually work in.

Example Windows:

```text
Workspace directory ❯ E:\sol-lite-WS\1
```

Example macOS:

```text
Workspace directory ❯ /Users/yourname/Projects/MyProject
```

The selected directory becomes the filesystem boundary for that session.

## 10. First-run checks

Inside SOL-Lite run:

```text
/help
/agents
/workspace
/workspaces
/sessions
/skills
/tools
/status
```

You should see the built-in command surface and the skills available to the active agent/workspace.

## 11. First safe agent request

Paste:

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

This validates workspace access, session context, agent loading, Ollama communication, native structured tools and read-only policy.

## 12. Test skill routing

Ask:

```text
Debug this problem using a reproduce → isolate → root-cause → fix → validate workflow. Do not make unrelated changes.
```

Then:

```text
/skills show systematic-debugging
```

The first request should naturally use relevant debugging guidance. The second directly displays the skill instructions.

## 13. Test verbose/debug display

```text
/verbose
```

Run a normal task and observe round/tool/activity information.

Then:

```text
/debug
```

Use debug mode when diagnosing a runtime issue. Return to normal with:

```text
/normal
```

## 14. Test a controlled background task

```text
/background Inspect the repository test structure and identify the safest test entry points. Do not modify files.
```

Then:

```text
/tasks
```

## 15. Test the permission boundary

Ask the agent to perform a harmless file mutation only if you want to test approval. For example:

```text
Create a file named sol-lite-approval-test.txt containing exactly TEST.
```

The mutation should be subject to the configured filesystem approval policy. Do not approve it unless you intend to create the file.

## 16. Test SearXNG from the agent

With SearXNG enabled, ask:

```text
Search the web for the official Python documentation for virtual environments. Prefer the primary official documentation source and explain which result supports the answer.
```

The network request is still governed by SOL-Lite's network permission/approval policy.

## 17. Run the automated tests

Windows:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe scripts\audit-pack.py
.\scripts\battle-test.bat
```

macOS:

```bash
./.venv/bin/python -m compileall -q src tests
./.venv/bin/python -m pytest -q
./.venv/bin/python -m ruff check src tests
./.venv/bin/python scripts/audit-pack.py
./scripts/battle-test.command
```

## 18. Live model smoke test

Windows:

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_engineer
```

macOS:

```bash
./.venv/bin/python -m sol_lite battle-test --live --agent sol_engineer
```

This requires a running, reachable Ollama service and the selected model.

## 19. Normal daily startup

Windows:

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
.\scripts\start.bat
```

macOS:

```bash
cd /path/to/SOL-Lite-v0.2.5
./scripts/start.command
```

Inside the session:

```text
/status
/workspace
/skills
```

Then describe the task. You normally do not manually activate a skill.

## 20. When something goes wrong

Do not immediately reinstall. Use:

```text
/verbose
/debug
/doctor
```

Then classify the failure:

```text
workspace
model/Ollama
tool
permission/approval
network/SearXNG
skill
terminal UI
task/cancellation
```

Capture the exact error, reproduce it, isolate the root cause, apply the smallest fix, then rerun the failing test and adjacent regression tests.

## 21. Complete command reference

See [Dummies Command List](../user/dummies-command-list.md).

## 22. Complete skill reference

See [Complete Skills Catalogue and Daily Use](../user/skills-full-catalog.md).
