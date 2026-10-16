# SOL-Lite: beginner setup and first run

For terminal basics, normal versus elevated access, configuration editing and a full battle sequence, start with [Zero-to-battle](zero-to-battle-noob-runbook.md). **Current checkout blocker:** `scripts/preflight.py` requires 39 built-in skills but this checkout has 40. The installer is expected to stop at that contract until a maintainer resolves it; the success output below describes the intended passing state, not an observed result.

For the v0.2.6 source tree. Checked by reading code and scripts, without running installation, application or tests. Commands below are instructions for the reader.

Continue with the [complete user guide](../user/beginner-user-guide.md) and [system guide](../architecture/beginner-system-guide.md).

To update all agents and configure optional capabilities, continue to [full feature configuration](full-feature-configuration.md). Then use the [first-session walkthrough](first-session-walkthrough.md) and [starter prompt packs](../user/starter-prompt-packs.md).

## 🚀 1. Absolute prerequisites

SOL-Lite is a terminal application using local Ollama models. There is no SOL-Lite browser homepage. Standalone startup needs no PostgreSQL, Redis, Docker, Microsoft Office or SOL-Command account.

This primary path is for 64-bit Windows:

1. Install **Python 3.12** from [Python downloads](https://www.python.org/downloads/). Enable the Python launcher and PATH option. The manifest requires **Python >=3.11**, without an exact patch pin. This guide selects 3.12 because the supplied voice installer includes Kokoro only below Python 3.13.
2. Install [Git for Windows](https://git-scm.com/install/windows) with standard defaults.
3. Install [Ollama for Windows](https://ollama.com/download/windows) and open Ollama from Start. No server version is pinned; the Python client dependency is `ollama>=0.6.3`.
4. Obtain company account/network access to `git.corp.pacenlife.com`. The clone address below comes from this checkout's remote and is not a public download.
5. Close old terminals and open **Windows PowerShell** from Start.

Verify one command at a time:

```powershell
py -3.12 --version
git --version
ollama --version
```

Expect Python 3.12.x and version output from the other commands. Stop if a command is missing.

The configured models include 27B and 30B parameter models. Downloads and memory requirements are substantial. The repository declares no dependable minimum RAM, GPU or disk capacity; installation success cannot establish that all models fit in memory.

## 📥 2. Clean slate installation

Run each line separately and stop on errors:

```powershell
Set-Location $env:USERPROFILE
git clone https://git.corp.pacenlife.com/plg-sol/PLG_Ai_Lite
Set-Location .\PLG_Ai_Lite
py -3.12 install\common\install.py
```

This invokes the common installer used by `scripts/setup.bat`, explicitly choosing Python 3.12. It creates `.venv`, upgrades its pip, and runs `pip install -e .[dev,voice]`. Do not repeat `pip install -e .` afterwards.

**When you run the installer**, it also attempts eSpeak-NG installation through winget and downloads voice weights. It can therefore change machine-level software. Voice preparation errors can be recorded without stopping text-chat installation.

Look near the end for:

```text
SOL-Lite preflight: PASS (version=0.2.6, Rich=..., skills=39)
SOL-Lite installation state written: ...\data\state\install.json
```

The dots represent installation-specific values. Keep the complete checkout: this editable installation needs the source, config, prompts and skills. Copying `.venv` alone is not an installation.

Keep Ollama open and download the models from `config/models.yaml`:

```powershell
ollama pull qwen3.5:9b
ollama pull qwen3-coder:30b
ollama pull qwen3.5:27b
ollama pull nomic-embed-text:latest
ollama list
.\.venv\Scripts\python.exe -m sol_lite diagnose
```

Read the diagnostic JSON. `api_version.ok` and `models.ok` should be true; `models.missing` should be empty. Its overall success status does not require an empty missing-model list and does not test generation under memory load.

## ⚙️ 3. Environment and configuration map

**Zero environment variables are required for standalone startup.** Leave `.env` absent, or create it with this entire content:

```dotenv
# Standalone startup uses the checked-in YAML defaults; no variables are required.
```

Do not fill optional credentials from `.env.example` just to start chat. Leave search, NAS, platform integrations and bridge disabled until needed. `SOL_INSTANCE_ID` and `SOL_INSTANCE_KEY` are rejected; pairing credentials belong in the OS keyring.

Bootstrap requires these files, even when their feature is unused:

```text
config/sol-lite.yaml
config/permissions.yaml
config/agents.yaml
config/models.yaml
config/schedules.yaml
config/logging.yaml
config/searxng.yaml
```

`remote-nodes.yaml` is optional. Defaults use `workspace/` for work, `data/` for local state and `logs/` for logs. Runtime creates its configured directories. The checkout must be writable.

Windows user overrides live at `%APPDATA%\SOL-Lite\settings.yaml`. They can override models and preferences. Permissions remain in repository policy. See [configuration](../architecture/configuration.md) for every supported variable and merge rule.

## 🏃 4. First-time launch

From the repository directory:

```powershell
.\.venv\Scripts\python.exe -m sol_lite start --agent sol_pa --workspace .\workspace
```

Startup creates the default workspace before opening the session. A different arbitrary workspace must already exist.

The source-defined banner includes:

```text
SOL-Lite
Local-first multi-agent engineering runtime
SOL PA · ...
Model qwen3.5:9b · Shells ...
```

The banner confirms the shell opened, not that a model answered. Enter these inside SOL-Lite:

```text
/workspace
/agents
/skills list
```

Then send:

```text
Inspect this workspace using read-only tools. Report its actual path and files. Do not run terminal commands or create or change files.
```

Check the tool output supporting the response. An empty workspace is normal. `/quit` exits.

**No browser URL is needed.** `http://127.0.0.1:11434` is Ollama's endpoint. The configured bridge port `8787` is disabled and is not a SOL-Lite webpage.

For daily startup, open PowerShell:

```powershell
Set-Location "$env:USERPROFILE\PLG_Ai_Lite"
.\launcher\windows\SOL-Lite.cmd
```

Choose a recent workspace or enter an existing folder. Normal launch does not install dependencies. Confirm `/workspace` before work.

## 🛑 5. Code-inferred troubleshooting

These signatures are predicted from code, not observed in live testing.

### Ollama is closed

**Likely error:** `Ollama chat failed: ...` with connection refusal or failure; exact underlying wording depends on the client.

**One-step fix:** Open Ollama from Start.

### The PA model is missing

**Likely error:** `Ollama chat failed: model 'qwen3.5:9b' not found ...`.

**One-step fix:** Run `ollama pull qwen3.5:9b` in PowerShell. For another agent, pull the model named in its error.

### The selected workspace does not exist

**Source-defined error:** `Workspace directory does not exist: ...`, possibly prefixed by `Workspace error:`.

**One-step fix:** Create that exact folder in File Explorer before selecting it again.

For other failures, use [troubleshooting](../user/troubleshooting.md). Battle tests are a maintainer acceptance workflow, not a prerequisite for first chat.

## macOS equivalent

This section is for a Mac, not another Windows step. Install Python 3.12 from [Python](https://www.python.org/downloads/), Git through Apple's Command Line Tools, and [Ollama for macOS](https://ollama.com/download/mac). Open Ollama. If Git is missing, run `xcode-select --install` in Terminal and finish Apple's installer first.

Run one line at a time:

```bash
python3.12 --version
git --version
ollama --version
cd "$HOME"
git clone https://git.corp.pacenlife.com/plg-sol/PLG_Ai_Lite
cd PLG_Ai_Lite
python3.12 install/common/install.py
ollama pull qwen3.5:9b
ollama pull qwen3-coder:30b
ollama pull qwen3.5:27b
ollama pull nomic-embed-text:latest
.venv/bin/python -m sol_lite diagnose
.venv/bin/python -m sol_lite start --agent sol_pa --workspace ./workspace
```

Later, enter the checkout and use `.venv/bin/python -m sol_lite start`. The common installer attempts eSpeak-NG through Homebrew only if Homebrew exists; missing voice support need not stop text chat. The separate app-launcher installation is in [macOS setup](macos.md).
