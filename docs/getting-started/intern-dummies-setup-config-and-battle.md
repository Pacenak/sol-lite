# SOL-Lite intern guide: configure, set up, and run the first full battle

**Updated entry point:** use [Zero-to-battle](zero-to-battle-noob-runbook.md) and [First full battle run](../testing/first-full-battle-run.md) for current terminal setup, gate order, logging and all-feature checks. This older chapter retains useful skill prompts, but its 39-skill count is historical: this checkout has 40 while preflight still expects 39. Do not mark a pass or remove a skill to hide that mismatch. Role-path writes can occur without an approval popup, and saved integration status is not a live-operation pass.

This is the copy-paste path for a new intern. It covers a standalone SOL-Lite install, the configuration you are allowed to check, and the first battle of all four agents and all 39 built-in skills.

SOL-Command is not required. Leave it unpaired for this battle.

Work from the SOL-Lite project directory. Do not point an agent at a personal folder, a production repository, or the whole disk.

The shorter command sheet is [Beginner command list](../user/dummies-command-list.md). The release runbook is [Full battle test](../testing/battle-test-guide.md). This page is the first intern run.

## Lab sheet

Fill this in before you start. Attach it to the score sheet at the end.

| Item | Your value |
|---|---|
| Date and timezone | |
| Your name | |
| Operating system | Windows or macOS |
| SOL-Lite folder | |
| `sol-lite version` | |
| Git commit (`git rev-parse --short HEAD`) | |
| Python version | |
| Disposable battle folder | |
| Ollama running | yes or no |

## Rules for this battle

1. The disposable battle folder is the only place an agent may create a file.
2. Deny any approval whose target is outside that folder.
3. A missing optional service is `BLOCKED`. It is not a pass.
4. If the agent claims a file, a test, or a search result, open the file or read the tool result before you mark `PASS`.
5. Skills do not grant permission. An agent still needs approval for writes and for network calls.
6. Do not edit `config/permissions.yaml` for this run. Do not enable the `bridge` listener. Do not pair SOL-Command.

## 1. Confirm you are in the project

Windows PowerShell:

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
Get-ChildItem
```

macOS:

```bash
cd ~/git/PLG_Ai_Lite
ls
```

You need `pyproject.toml`, `src`, `tests`, `config`, `scripts`, `skills`, and `docs`. Use your real project path if it is different. Write that path on the lab sheet.

## 2. Check the machine

Windows:

```powershell
python --version
git --version
ollama --version
```

macOS:

```bash
python3 --version
git --version
ollama --version
```

You need Python 3.11 or newer, Git, and Ollama. If `ollama version` fails, install Ollama and start it before the live battle. The automated gate can still be attempted, and a missing Ollama model later is `BLOCKED` for the live rows only.

## 3. Install

Windows, from the project directory:

```powershell
.\scripts\setup.bat
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m sol_lite version
.\.venv\Scripts\python.exe -m sol_lite doctor
```

macOS:

```bash
chmod +x scripts/*.command install/macos/*.command
./scripts/setup.command
.venv/bin/python -m pip install -e .
.venv/bin/sol-lite version
.venv/bin/sol-lite doctor
```

`doctor` must finish without a traceback. On a machine that has never paired, the SOL-Command line reads `not paired (standalone)`. That is the expected state for this guide.

The version printed by `sol-lite version` must match `application.version` in `config/sol-lite.yaml`. The current tree uses `0.2.6`. Write the printed version on the lab sheet.

## 4. Configuration you check, and configuration you leave alone

Read these files. Change one only when this section says you may.

### `config/sol-lite.yaml`

This is the product runtime file.

| Setting | First-battle value | What you do |
|---|---|---|
| `application.version` | `0.2.6` | Compare it with `sol-lite version`. Do not edit it to hide a mismatch. |
| `runtime.max_tool_calls_per_task` | `40` | Leave it. This is a safety ceiling. |
| `skills.builtin_root` | `skills` | Leave it. Built-in skills load from that folder. |
| `workspace.root` | `./workspace` | Leave the file. Point the battle at a disposable folder with `--workspace` or `SOL_WORKSPACE_ROOT`. |
| `bridge.enabled` | `false` | Leave it false. This is a local listener. It is not SOL-Command pairing. |
| `background.enabled` | `false` | Leave it. |
| `macos.integrations_enabled` and `windows.integrations_enabled` | `false` | Leave them. |

### `config/models.yaml`

Local Ollama is the provider. The endpoint is `http://127.0.0.1:11434`.

| Profile | Model | Used by |
|---|---|---|
| `fast` | `qwen3.5:9b` | SOL PA |
| `engineer` | `qwen3-coder:30b` | SOL Engineer |
| `reviewer` | `qwen3.5:27b` | SOL Business and SOL Docs |
| `embedding` | `nomic-embed-text:latest` | Embedding work when a tool asks for it |

Check what is already installed:

```text
ollama list
```

Pull a model only when `ollama list` does not already show that name. Do not pull a second copy under a different name and then edit the profile unless a senior tells you to.

```text
ollama pull qwen3.5:9b
ollama pull qwen3-coder:30b
ollama pull qwen3.5:27b
ollama pull nomic-embed-text
```

Confirm the API:

Windows: `curl.exe http://127.0.0.1:11434/api/tags`

macOS: `curl http://127.0.0.1:11434/api/tags`

A good result is JSON that lists models.

### `config/agents.yaml`

Four agents are enabled. Do not add an agent for this battle.

| Id | Name | Model profile | First battle job |
|---|---|---|---|
| `sol_pa` | SOL PA | `fast` | Planning, research, handoffs |
| `sol_business` | SOL Business | `reviewer` | Project and product planning |
| `sol_docs` | SOL Docs | `reviewer` | Documents, slides, sheets, diagrams |
| `sol_engineer` | SOL Engineer | `engineer` | Code, tests, Git inspection, shell, studio file changes |

Built-in skills are available to every agent. You still switch to the agent in the table so the battle uses the intended model.

Studio manuals, lab and production hosts, and file backups are a separate staff path: [Studio change gate](../user/studio-change.md). Do not point that work at a production host during the first battle.

### `config/searxng.yaml` and `.env.example`

SearXNG starts disabled (`enabled: false`). Leave it disabled unless a senior gives you a private SearXNG URL. The web-research skill row is `BLOCKED` when it is disabled.

`.env.example` lists **environment variables the runtime actually reads** (paths, Ollama, SearXNG, integration CLI helpers, CI flags). Model names and approval policy stay in `config/models.yaml` and `config/permissions.yaml` — not in `.env`. You do not need a `.env` file for the first battle. If `SOL_WORKSPACE_ROOT` is already set in your shell, know that the live smoke uses it. Set it yourself in section 6 so the smoke reads the disposable folder. Full reference: [Configuration](../architecture/configuration.md).

### Files you do not edit

- `config/permissions.yaml` — reads, writes, shell, and network approval.
- `config/logging.yaml` — log destination.
- Anything under `src/` during this battle.

## 5. Make the disposable battle folder

Windows:

```powershell
New-Item -ItemType Directory -Force E:\sol-lite-battle\intern-1 | Out-Null
Set-Content E:\sol-lite-battle\intern-1\hello.txt "battle-marker-intern"
Set-Content E:\sol-lite-battle\intern-1\sample.py @"
def add(a, b):
    return a - b
"@
```

macOS:

```bash
mkdir -p "$HOME/sol-lite-battle/intern-1"
printf 'battle-marker-intern\n' > "$HOME/sol-lite-battle/intern-1/hello.txt"
printf 'def add(a, b):\n    return a - b\n' > "$HOME/sol-lite-battle/intern-1/sample.py"
```

`sample.py` is wrong on purpose. `add` subtracts. Later prompts may describe a fix. For the read-only rows, tell the agent not to edit the file.

## 6. Automated battle, then one live smoke per agent

From the project directory, using the project virtual environment.

Windows automated gate:

```powershell
.\.venv\Scripts\python.exe -m sol_lite battle-test
```

macOS automated gate:

```bash
.venv/bin/python -m sol_lite battle-test
```

This runs, in order, and stops at the first failure:

1. `scripts/audit-pack.py`
2. `scripts/preflight.py` (version match and 39 built-in skills)
3. `python -m compileall -q src tests`
4. `python -m pytest -q`
5. `python -m ruff check src tests`

The last line of a good run is `SOL-Lite battle test: PASS`. Save the output. A failure here is `FAIL` for the automated row. Fix nothing in the product unless a senior asks. Record the failing command and the last error.

The same command with `--live` repeats that whole gate, then asks one agent to call `inventory_workspace` once and report how many files it found. It does not modify files. It passes only when the audit log contains `workspace.inventory` and the process then prints `LIVE AGENT PASS: <agent>` and `SOL-Lite battle test: PASS`.

Point that smoke at the disposable folder for the current shell.

Windows, once per agent:

```powershell
$env:SOL_WORKSPACE_ROOT = "E:\sol-lite-battle\intern-1"
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_pa
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_business
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_docs
.\.venv\Scripts\python.exe -m sol_lite battle-test --live --agent sol_engineer
```

macOS:

```bash
export SOL_WORKSPACE_ROOT="$HOME/sol-lite-battle/intern-1"
.venv/bin/python -m sol_lite battle-test --live --agent sol_pa
.venv/bin/python -m sol_lite battle-test --live --agent sol_business
.venv/bin/python -m sol_lite battle-test --live --agent sol_docs
.venv/bin/python -m sol_lite battle-test --live --agent sol_engineer
```

Each live command repeats pytest. That is expected. A missing model is `BLOCKED` for that agent, with the Ollama error saved. `hello.txt` must still contain `battle-marker-intern` after all four runs.

There is also a wrapper that runs the automated gate without `--live`:

Windows: `.\scripts\battle-test.bat`

macOS: `./scripts/battle-test.command`

## 7. Open the terminal for the skill battle

Windows:

```powershell
.\.venv\Scripts\python.exe -m sol_lite start --workspace E:\sol-lite-battle\intern-1 --agent sol_pa
```

macOS:

```bash
.venv/bin/python -m sol_lite start --workspace "$HOME/sol-lite-battle/intern-1" --agent sol_pa
```

Inside the terminal:

```text
/workspace
/agents
/skills list
/doctor
```

`/workspace` must show the disposable folder. `/agents` must list `sol_pa`, `sol_business`, `sol_docs`, and `sol_engineer`. `/skills list` must include the built-in skills. If the workspace is the SOL-Lite source tree, quit and start again with `--workspace`.

Switch agent with `/use sol_engineer`, `/use sol_business`, `/use sol_docs`, or `/use sol_pa`.

Before each skill prompt, run:

```text
/skills show <skill-id>
```

`PASS` for a skill row means `/skills show` printed that skill, the agent answered the prompt, and the evidence matches the files you can see. A claim with no tool result is `FAIL`.

Quit with `/quit` when the score sheet is full.

## 8. One safe prompt for each agent

Run these before the skill list. Stay in the disposable workspace.

### SOL PA

```text
/use sol_pa
```

```text
Plan a one-hour intern battle in this workspace. List the four agents, the order you would test them, and one risk. Do not modify files. Do not use SOL-Command.
```

`PASS`: the plan names `sol_pa`, `sol_business`, `sol_docs`, and `sol_engineer`, and no file in the folder changed.

### SOL Business

```text
/use sol_business
```

```text
Read hello.txt and sample.py. Write a five-line status note in your answer: what the folder contains, what sample.py claims to do, and what it actually returns. Do not modify files.
```

`PASS`: the note says `hello.txt` contains `battle-marker-intern` and that `add` returns `a - b`.

### SOL Docs

```text
/use sol_docs
```

```text
Create one short DOCX report in this workspace named intern-battle-note.docx. Include the text battle-marker-intern and one sentence about sample.py. Do not write anywhere else.
```

Approve only if the target path is inside the disposable folder. `PASS`: the docx exists there and `hello.txt` is unchanged. If artifact dependencies are missing, record the exact error as `BLOCKED` and continue. Setup for documents is in [Artifacts](../user/artifacts.md).

### SOL Engineer

```text
/use sol_engineer
```

```text
Inspect sample.py. Explain the bug in add. Propose the one-line fix. Do not modify the file. Do not run a command that writes.
```

`PASS`: the answer says the function subtracts, and `sample.py` on disk still contains `return a - b`.

## 9. First battle of every built-in skill

There are 39 skills. The folder name and the `name` in `SKILL.md` match. Preflight fails if that count is not 39.

For every row: `/use` the agent, `/skills show` the skill id, paste the prompt, then mark the score sheet.

Read-only prompts must leave `hello.txt` and `sample.py` unchanged. Artifact prompts may add one file inside the disposable folder. Deny any other write.

### SOL PA skills

`agent-evaluation`

```text
Use the agent-evaluation skill. Score the SOL Engineer sample.py inspection you would expect on tool use, evidence, and safety. Do not modify files. Do not claim a tool ran unless this session shows a tool result.
```

`career-operations`

```text
Use the career-operations skill. Turn this intern battle into three evidence items I can show a senior. Do not modify files. Do not invent results from sections I have not run.
```

`handoff`

```text
Use the handoff skill. Write a handoff from SOL PA to SOL Engineer for the sample.py subtraction bug. Include status, evidence, and the next action. Do not modify files.
```

`humanizer`

```text
Use the humanizer skill. Rewrite this sentence so it is clearer and still true: "The function add is currently implemented as subtraction and the battle marker file was not edited." Do not modify files.
```

`planning-and-estimation`

```text
Use the planning-and-estimation skill. Estimate the remaining skill rows on this score sheet. State what is uncertain. Do not modify files.
```

`product-discovery`

```text
Use the product-discovery skill. State the user problem this intern battle is checking, one hypothesis, and what evidence would confirm it. Do not modify files.
```

`product-management`

```text
Use the product-management skill. Write acceptance criteria for "intern can battle-test SOL-Lite without SOL-Command." Do not modify files.
```

`prompt-engineering`

```text
Use the prompt-engineering skill. Write one prompt that asks SOL Engineer to inspect sample.py, forbids edits, and requires file evidence. Do not run that prompt and do not modify files.
```

`web-research-searxng`

Leave SearXNG disabled. Mark this row `BLOCKED` unless a senior enabled a private SearXNG URL. If it is enabled, ask for one current Python version fact, approve the network call, and `PASS` only when the tool result contains sources. A guessed version with no tool result is `FAIL`.

`web-source-verification`

```text
Use the web-source-verification skill. I claim hello.txt contains battle-marker-intern. Verify that from the workspace file. If you cannot check the web, say so. Do not modify files.
```

`PASS` requires the file check. A web search is optional and stays `BLOCKED` when SearXNG is off.

`studio-odoo-import`

```text
Use the studio-odoo-import skill. This workspace has no Studio Odoo source files and no studio root. Name the first tool you would call. Say that you will not invent a studio path, a tax code, or an import row. Do not bind a path. Do not write files.
```

`PASS`: the answer names `studio_odoo_bind` or says the studio root is missing, and `hello.txt` is unchanged. A guessed tax code or a written CSV is `FAIL`.

### SOL Business skills

`agile-sprint-planning`

```text
Use the agile-sprint-planning skill. Plan a one-day sprint whose only outcome is this intern battle score sheet. Include what would carry over if Ollama is down. Do not modify files.
```

`copilot-patterns`

```text
Use the copilot-patterns skill. Give me one reusable instruction I can paste before any read-only workspace task. Do not modify files.
```

### SOL Docs skills

`book-to-skill`

```text
Use the book-to-skill skill. The only source is hello.txt in this workspace. Outline a tiny skill that says how to check that marker. Do not copy any other book. Do not write a skill into the SOL-Lite repository. Do not modify hello.txt.
```

`diagram-design`

```text
Use the diagram-design skill. Describe a four-box diagram named SOL PA, SOL Business, SOL Docs, and SOL Engineer. Do not guess delegation rules. Do not modify files.
```

`document-layout`

```text
Use the document-layout skill. If intern-battle-note.docx already exists, describe its heading structure. If it does not, create that one DOCX in this workspace with the heading Intern battle and the line battle-marker-intern. Do not write anywhere else.
```

`documentation-engineering`

```text
Use the documentation-engineering skill. From hello.txt and sample.py only, draft a five-line README for this battle folder. Put it in the answer. Do not modify files.
```

`mermaid-diagrams`

```text
Use the mermaid-diagrams skill. Produce one Mermaid flowchart of this battle: setup, doctor, automated battle, live smoke, skill rows. Do not modify files.
```

`presentation-design`

```text
Use the presentation-design skill. Create one PPTX in this workspace named intern-battle.pptx with one title slide that contains battle-marker-intern. Do not write anywhere else.
```

`spreadsheet-reporting`

```text
Use the spreadsheet-reporting skill. Create one XLSX in this workspace named intern-battle.xlsx with columns Skill, Agent, and Result, and one example row for repository-analysis. Do not write anywhere else.
```

`ui-ux-design`

```text
Use the ui-ux-design skill. Review the intern score sheet as a text form. Name three fields that must be filled before the battle starts. Do not modify files.
```

If a DOCX, PPTX, or XLSX tool reports a missing dependency, mark that one row `BLOCKED` and keep the exact message.

### SOL Engineer skills

`agent-skill-curation`

```text
Use the agent-skill-curation skill. List how a built-in skill differs from an imported skill. Inspect this workspace only. Do not import or remove any skill. Do not modify files.
```

`architecture-design`

```text
Use the architecture-design skill. Describe SOL-Lite as a local runtime with four agents and a workspace boundary. Name one failure mode if the workspace path is wrong. Do not modify files.
```

`code-review`

```text
Use the code-review skill. Review sample.py. Report the defect with the function name and the return expression. Do not modify the file.
```

`debugging-error-recovery`

```text
Use the debugging-error-recovery skill. Assume a tool said sample.py was missing, but the file is in this workspace. State the recovery step and then read the file. Do not modify files.
```

`debugging-methodology`

```text
Use the debugging-methodology skill. Walk reproduce, isolate, and root cause for add(2, 1) returning 1. Do not modify files.
```

`git-workflow`

```text
Use the git-workflow skill. If this workspace is not a Git repository, say that and stop. Do not run git init. Do not commit. Do not modify files.
```

`PASS`: the answer says the disposable folder is not a Git repository, unless you deliberately made it one. Do not let the agent operate on the SOL-Lite checkout.

`harness-audit`

```text
Use the harness-audit skill. From this session, state whether /skills show worked and whether writes require approval. Do not change configuration. Do not modify files.
```

`infrastructure-discovery`

```text
Use the infrastructure-discovery skill. Report only the workspace path and whether hello.txt is present. Do not scan the machine outside this workspace. Do not modify files.
```

`open-code-review`

```text
Use the open-code-review skill. Review sample.py for correctness only. Quote the buggy return line. Do not modify files.
```

`performance-investigation`

```text
Use the performance-investigation skill. State what you would measure before calling add slow. Do not invent timings. Do not modify files.
```

`refactoring`

```text
Use the refactoring skill. Propose a behaviour-preserving note: the bugfix would change subtraction to addition, so it is not a refactor. Do not modify files.
```

`repository-analysis`

```text
Use the repository-analysis skill. Inventory this workspace. Report the file names you can prove. Do not modify files.
```

`PASS`: both `hello.txt` and `sample.py` are named from tool output.

`security-audit`

```text
Use the security-audit skill. Read hello.txt and confirm it is inside this workspace. Do not request a delete. Do not modify files.
```

`shell-engineering`

```text
Use the shell-engineering skill. Print the workspace path with a read-only directory listing. Do not create, delete, or overwrite anything.
```

Approve only a listing command whose target is the disposable folder.

`skill-import`

```text
Use the skill-import skill. Explain the discover, then import, sequence. Do not discover a remote source. Do not import or remove a skill. Do not modify files.
```

`systematic-debugging`

```text
Use the systematic-debugging skill. Show that add(2, 1) is 1 because the function returns a - b. Read sample.py. Do not modify it.
```

`test-engineering`

```text
Use the test-engineering skill. Write a pytest-style test in the answer that would fail on the current add. Do not create the test file.
```

## 10. Optional rows

Mark these `NOT RUN` unless a senior hands you a lab account. They are outside the first battle.

| Check | Command | Pass when |
|---|---|---|
| SOL-Command pair | `sol-lite connect` | A lab administrator approved the instance, and `sol-lite command-status` shows sectors. Then `sol-lite disconnect`. |
| SearXNG | enabled private URL | A search tool result lists sources. |
| Google | `sol-lite google-connect` | `sol-lite google-status` shows the lab account. |
| Jira | `sol-lite jira-connect` | `sol-lite jira-status` lists the granted lab project. |
| Studio Odoo | bind a lab checkout from [the beginner guide](../user/dummies-studio-odoo.md) | `studio_odoo_status` shows `templates_ok` and `odoo_api: not used`. No IRD values in the score sheet. |
| Voice | `sol-lite voice-status` | The command prints readiness without a traceback. |

Do not paste invite codes, tokens, or personal mail into the score sheet. The beginner pairing runbook is [Link SOL-Lite to SOL-Command](../user/dummies-command-link.md). Technical detail is in [SOL-Lite integration](../integrations/sol-lite.md).

## 11. Score sheet

Copy this table into your notes. Use only `PASS`, `FAIL`, `BLOCKED`, or `NOT RUN`.

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | `sol-lite doctor` shows standalone | | |
| 2 | Version matches `config/sol-lite.yaml` | | |
| 3 | `ollama list` shows the four profile models | | |
| 4 | Automated `sol-lite battle-test` | | |
| 5 | Live smoke `sol_pa` | | |
| 6 | Live smoke `sol_business` | | |
| 7 | Live smoke `sol_docs` | | |
| 8 | Live smoke `sol_engineer` | | |
| 9 | `/workspace` is the disposable folder | | |
| 10 | Agent prompt: SOL PA | | |
| 11 | Agent prompt: SOL Business | | |
| 12 | Agent prompt: SOL Docs | | |
| 13 | Agent prompt: SOL Engineer | | |
| 14 | `agent-evaluation` | | |
| 15 | `agent-skill-curation` | | |
| 16 | `agile-sprint-planning` | | |
| 17 | `architecture-design` | | |
| 18 | `book-to-skill` | | |
| 19 | `career-operations` | | |
| 20 | `code-review` | | |
| 21 | `copilot-patterns` | | |
| 22 | `debugging-error-recovery` | | |
| 23 | `debugging-methodology` | | |
| 24 | `diagram-design` | | |
| 25 | `document-layout` | | |
| 26 | `documentation-engineering` | | |
| 27 | `git-workflow` | | |
| 28 | `handoff` | | |
| 29 | `harness-audit` | | |
| 30 | `humanizer` | | |
| 31 | `infrastructure-discovery` | | |
| 32 | `mermaid-diagrams` | | |
| 33 | `open-code-review` | | |
| 34 | `performance-investigation` | | |
| 35 | `planning-and-estimation` | | |
| 36 | `presentation-design` | | |
| 37 | `product-discovery` | | |
| 38 | `product-management` | | |
| 39 | `prompt-engineering` | | |
| 40 | `readable-plans` | | |
| 41 | `refactoring` | | |
| 42 | `repository-analysis` | | |
| 43 | `security-audit` | | |
| 44 | `shell-engineering` | | |
| 45 | `skill-import` | | |
| 46 | `spreadsheet-reporting` | | |
| 47 | `studio-odoo-import` | | |
| 48 | `systematic-debugging` | | |
| 49 | `test-engineering` | | |
| 50 | `ui-ux-design` | | |
| 51 | `web-research-searxng` | | |
| 52 | `web-source-verification` | | |
| 53 | `hello.txt` still says `battle-marker-intern` | | |
| 54 | `sample.py` still returns `a - b` | | |

The first battle is complete when rows 1–13 and 53–54 are filled, and every skill row from 14–52 is `PASS`, `FAIL`, or `BLOCKED` with a sentence of evidence. `NOT RUN` is allowed only for a skill your senior told you to skip, and for the optional services in section 10.

Hand the lab sheet, this score sheet, and the automated battle output to your senior. Do not commit product changes from this run.
