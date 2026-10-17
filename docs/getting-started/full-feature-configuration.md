# Full feature configuration and integration readiness

Start with [terminal/admin and configuration basics](zero-to-battle-noob-runbook.md) if you are new to PowerShell. **Current source blockers:** the 39-versus-40 skill preflight mismatch prevents an honest installer/battle pass; pack manifests also need reviewed reconciliation after payload changes. Follow the stop conditions in that chapter and the [first full battle run](../testing/first-full-battle-run.md).

For the v0.2.6 source tree. This runbook was prepared by static reading; nothing here has been installed, connected or tested by the documentation author. Commands are for the operator to run deliberately. Start with [base installation](full-setup-first-run.md), then follow this chapter in order. Use the [first-session walkthrough](first-session-walkthrough.md) and [starter prompt packs](../user/starter-prompt-packs.md) afterwards.

“Fully working” means every feature you intend to use has passed its own real check. Installing all Python packages does not supply external accounts, server access, model memory, credentials or administrator grants. Keep unavailable features marked blocked rather than reporting them as ready.

## 1. Update the source without losing work

Close SOL-Lite and preserve the actual workspaces, configuration, required `data/` state and per-user settings. Credentials stay in the OS keyring and need their own account recovery/reconnection process.

In PowerShell, from your checkout:

```powershell
git status --short
git branch --show-current
git remote -v
```

If status lists changes, stop the update and preserve/review them through your normal Git workflow. Do not reset, delete or overwrite local files. If the current branch and remote are the release you are supposed to use and the worktree is clean:

```powershell
git pull --ff-only
py -3.12 install\common\install.py --repair
.\.venv\Scripts\python.exe -m pip install -e ".[artifacts,google]"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m sol_lite version
```

The repair command already installs `.[dev,voice]`. The second install adds the two remaining declared extras, `artifacts` and `google`. There is no declared `mcp` extra. A version bump alone does not prove configuration or integration readiness. Dependencies are not locked to exact versions, so retain the release/commit and any reported compatibility error.

On macOS use `python3.12 install/common/install.py --repair` and `.venv/bin/python` in place of the Windows interpreter. Platform launcher repair procedures are in [repairing](repairing.md).

## 2. Refresh and verify model profiles

Keep Ollama open. These are the shipped model names, not a recommendation to replace them with arbitrary newer models:

```powershell
ollama pull qwen3.5:9b
ollama pull qwen3-coder:30b
ollama pull qwen3.5:27b
ollama pull nomic-embed-text:latest
ollama list
.\.venv\Scripts\python.exe -m sol_lite diagnose
```

Pull refreshes the named tags. Review `models.missing` explicitly; a successful diagnostic exit does not require this list to be empty. Each agent must also complete a real request: a downloaded model can still fail from insufficient memory or unsupported tool behavior.

The default `config/models.yaml` profile settings are:

- `fast`: `qwen3.5:9b`, temperature `0.2`, timeout `180` seconds; PA.
- `engineer`: `qwen3-coder:30b`, temperature `0.15`, timeout `600`; Engineer.
- `reviewer`: `qwen3.5:27b`, temperature `0.15`, timeout `600`; Business and Docs.
- `embedding`: `nomic-embed-text:latest`, temperature `0.0`, timeout `180`; embedding profile definition, not an automatic indexing service.

Keep these profiles initially. If hardware cannot run them, record the affected agent as blocked before choosing and validating a smaller tool-capable model. Merely declaring `tool_calling` in configuration does not add that ability to a model.

## 3. Configure the four standard agents

`config/agents.yaml` enables PA, Business, Docs and Engineer and binds their `model_profile`. Each agent also has its own `tools.yaml` and prompt under `src/sol_lite/agents/`. Updating the source updates these shipped definitions and built-in skills; it does not automatically review or update imported external skills.

In chat, open `/settings`. Categories in this source are:

1. General: default agent and general preferences.
2. Agents: enabled agents and profile selection.
3. Models & Ollama: provider and profile values.
4. Runtime: limits and timing.
5. Workspace & Data: paths.
6. Search / SearXNG.
7. Background & Integrations.
8. Terminal & Display.
9. View Configuration.

`J` opens Jira, `V` voice, `B` returns; `R` resets user settings and should not be selected casually. Saved overrides can conceal changes in shipped YAML. Review category 9 after an upgrade. Restart after direct file edits or integration connection changes.

For a fresh installation wanting explicit per-user agent bindings, this is a valid **partial user-settings mapping**, not the structure of `config/agents.yaml`:

```yaml
general:
  default_agent: sol_pa
models:
  provider:
    endpoint: "http://127.0.0.1:11434"
agents:
  agents:
    sol_pa:
      enabled: true
      model_profile: fast
    sol_business:
      enabled: true
      model_profile: reviewer
    sol_docs:
      enabled: true
      model_profile: reviewer
    sol_engineer:
      enabled: true
      model_profile: engineer
```

Merge this with existing user settings instead of replacing them. Windows path: `%APPDATA%\SOL-Lite\settings.yaml`; macOS: `~/Library/Application Support/SOL-Lite/settings.yaml`. The nested `agents.agents` shape matches the repository document merged by bootstrap.

## 4. Configuration layers and environment

Repository YAML loads first, then supported user overrides, then supported environment overrides. Start flags select initial session values. Bootstrap loads root `.env` without replacing an already-set process environment value. CLI connection commands may run before bootstrap: use explicit command arguments for OAuth JSON and Command URLs rather than assuming `.env` was loaded there.

No `.env` is required. For an explicit local configuration, these optional overrides are sufficient:

```dotenv
SOL_WORKSPACE_ROOT=./workspace # Default runtime working root, not every selected session folder.
SOL_DATA_ROOT=./data # Default local state root; some workflows retain checkout-rooted paths.
SOL_OLLAMA_URL=http://127.0.0.1:11434 # Local model service.
SOL_SEARXNG_ENABLED=false # Enable only after configuring a real JSON-enabled search service.
```

For advanced names and exact effects, use the [full configuration reference](../architecture/configuration.md). Model names belong in YAML/settings, not invented `SOL_FAST_MODEL` variables. Keep permissions in `config/permissions.yaml`; do not enable every scope to make a denied tool succeed.

Runtime defaults include four concurrent agent workers, a 40-tool-call safety ceiling and 900-second task timeout. These are limits, not goals. `schedules.yaml` defaults to disabled with no jobs; do not infer a durable scheduler from that file. Leave bridge/NAS/platform application automation disabled unless a separately implemented workflow needs them.

## 5. Artifact creation and exports

The `artifacts` extra above supplies DOCX, PPTX, XLSX and PDF-related libraries. Install [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) for Office-file PDF rendering. Install a supported Node.js LTS from [Node.js](https://nodejs.org/en/download), then in a new terminal:

```powershell
node --version
npm --version
npm install -g @mermaid-js/mermaid-cli
mmdc --version
```

Ask an agent to call `artifact_dependencies` and report each dependency. Then generate one new sample per format, validate it and render its previews. A dependency report alone is not a rendering pass. Open the files and previews; independently verify spreadsheet calculations. Use unique revision names because artifact outputs are not overwritten. [Artifact reference](../user/artifacts.md).

## 6. Local voice

Repair installs faster-whisper, Kokoro where supported, audio packages and voice setup. It attempts eSpeak-NG installation and weight downloads. Use:

```powershell
.\.venv\Scripts\python.exe -m sol_lite voice-status
```

In `/settings`, `V`, review detected providers. Preferences are in `data/state/voice.json`: `stt_enabled`, `stt_provider`, `stt_model`, `stt_language`, `tts_enabled`, `tts_provider`, `tts_voice`, `tts_speed`, `speak` and `endpoints`. The default STT model is `base`; Kokoro's default voice is `af_bella`. A platform speech fallback may be selected when local Kokoro is unavailable.

Grant microphone access in OS settings. In chat, `/listen` should recognise a harmless sentence; `/speak` toggles replies, so check the printed state before testing speech. A readiness probe is not proof that microphone capture or audio playback works.

Hosted voice is an alternative configuration, not necessary for local voice. An endpoint entry needs `base_url` and optionally `api_key_env`; select it using `endpoint:ENTRY_ID`. The adapters call `/audio/transcriptions` and `/audio/speech`. Obtain compatible endpoint credentials from its operator and keep values out of prompts. Do not select an unverified endpoint simply to make the settings look complete.

## 7. Private web search: SearXNG

Obtain the actual service base URL from its operator. This checkout does not install SearXNG. The server must enable `json` under `search.formats`. In `.env`, replace the placeholder before use:

```dotenv
SOL_SEARXNG_URL=https://YOUR_SEARCH_HOST # Your actual SearXNG base URL.
SOL_SEARXNG_ENABLED=true # Enables the agent search integration.
```

Verify in PowerShell:

```powershell
curl.exe "https://YOUR_SEARCH_HOST/search?q=Python&format=json"
```

Expect JSON rather than a login page or 403. Restart SOL-Lite and request an official-documentation search. Approve the exact network operation and inspect returned URLs. All four standard agents list the search tool. The shipped `10.10.40.10:30053` address is not a guaranteed service on your network. [Search details](../integrations/searxng.md).

## 8. Gmail and Google Calendar

**First time configuring Google itself?** Follow the [real-world Google setup chapter](../integrations/google-real-world-setup.md) for project creation, API enablement, consent, test users, scopes, Desktop OAuth download and actual read checks, with official Google documentation links.

The `google` extra is installed in section 1. You also need a Google account, a Google Cloud project, Gmail and Calendar APIs enabled, an OAuth consent configuration allowing that account, and a **Desktop app** OAuth client JSON saved outside the repository.

Using the real path:

```powershell
.\.venv\Scripts\python.exe -m sol_lite google-connect --client-secrets "C:\Users\YourName\Secrets\google-desktop.json"
.\.venv\Scripts\python.exe -m sol_lite google-status
```

Finish browser consent. OAuth uses a temporary loopback port, not a fixed SOL-Lite UI port. Tokens are saved to the OS keyring. Restart chat, select PA and request an approved read of a narrowly scoped inbox query or primary-calendar interval. Only that real request proves account access.

Scopes are Gmail read-only, Gmail send and owned-calendar events. Reads disclose private data and require approval; sends and calendar writes require exact approval of recipient/content/time details. No attachment workflow, automatic inbox monitor or recurring-event management is established by this integration. `google-disconnect` removes local saved authorization. [Google reference](../integrations/google-workspace.md).

## 9. Jira Cloud

Prepare the site URL, account email, API token and allowed project keys with your Jira administrator. From PowerShell:

```powershell
.\.venv\Scripts\python.exe -m sol_lite jira-connect
.\.venv\Scripts\python.exe -m sol_lite jira-status
```

Answer the prompts; the token goes into the OS keyring. Restart chat and use PA or Engineer. Bind/select the actual granted project through the Jira workspace tools when required. Ask for one approved read-only issue query before any write.

PA can plan/create/update/comment/transition inside granted projects. Engineer can read/update/comment/transition. Delete and assign are not provided. `doctor` reports saved state; `jira-status` is the live probe. To disconnect: `jira-disconnect --name CONNECTION_NAME`. [Jira reference](../integrations/jira.md).

## 10. SOL-Command pairing and skill packs

**Lite is a terminal client, not a website.** Follow [real-world terminal-to-Command linking](../integrations/command-real-world-linking.md) for the correct CLI/admin-browser split, mandatory network-sector setup and diagnostics when no pending request appears. The [static pairing analysis](../debugging/command-pairing-static-analysis.md) records confirmed visibility/recovery code issues and what remains unproven about a deployed failure.

Have the Command administrator supply the actual HTTPS base URL and a Lite invite, choose sectors and approve the pending instance. Replace both placeholders:

```powershell
.\.venv\Scripts\python.exe -m sol_lite connect --command-url https://YOUR_COMMAND_HOST --invite-code YOUR_INVITE
.\.venv\Scripts\python.exe -m sol_lite command-status
.\.venv\Scripts\python.exe -m sol_lite sync-skills
```

The connect operation waits for approval and claims the instance. Secrets are stored in the keyring. Restart chat. Only PA lists the Command tools. Verify assigned sectors before requesting their memories or metadata RAG search. This is not full vector retrieval or a local copy of Command memory.

Downloaded skills remain under `data/state/skills/pending/sol-command/`. Inspect their exact directories with `/skills discover`, then deliberately import reviewed packages. `/skills update ID` is separate from pulling application code; review the refreshed external source.

Jarvis requires a separate administrator grant and persona policy. Supported client domains are `meal_plans`, `fitness_plans`, `skills`, `memories`, `home_pa` and `code_fix`. A submission stays pending; Lite cannot approve/apply it. Disconnect removes local credentials; server revocation is separate. [Admin/operator runbook](../user/dummies-command-link.md).

## 11. Git, remotes and pull requests

Git must be installed and authenticated for the actual hosting server. Open the real checkout as workspace. Review the remote-trust prompt before accepting it; do not blanket-trust the entire disk.

Engineer exposes repository tools. Ask for read-only status/diff/remotes first. Pull/merge needs an appropriate clean tree; preserve unrelated work. Local edits/commits and remote writes have their own permission checks.

GitHub hosting tools additionally require the GitHub CLI, available at [GitHub CLI](https://cli.github.com/), authenticated to the correct server:

```powershell
gh --version
gh auth login
gh auth status
```

A corporate Git remote is not proof that its host supports GitHub APIs or `gh`. Verify the hosting platform before promising PR creation. Local Git can work while PR integration is blocked. [Repository workflows](../operations/repository-workflows.md).

## 12. Remote hosts and procedure manuals

Choose the standard SSH path for a Linux lab host. Install/enable the OS OpenSSH client, obtain the lab username and set up host-key trust and authentication outside SOL-Lite. Verify `ssh -V`. The app uses the system SSH agent/config; do not put private keys or passwords in YAML.

Merge an actual node into `config/remote-nodes.yaml`, replacing placeholders:

```yaml
nodes:
  - id: lab-linux
    hostname: YOUR_LAB_HOST
    platform: linux
    transport: ssh
    username: YOUR_LAB_USER
    port: 22
    environment: lab
    enabled: true
```

Restart. Ask PA or Engineer to list configured nodes, then approve one harmless read such as `uname`. Remote writes are a separate step. Production and missing environment labels remain inspect-only in the Studio write gate.

Windows `powershell` transport instead uses existing Windows remoting through `Invoke-Command`; remote configuration and authentication must already work. Although `http_api` is an enum value, the current remote manager raises `NotImplementedError` for it. Use SSH or PowerShell rather than configuring HTTP remote execution.

Put procedure manuals inside the selected workspace. `/follow manual.md` is dry inspection. PA can load/status/acknowledge; Engineer also has advance and Studio change tools. Secrets in approved manual commands resolve by name from the `plg-studio` keyring or process environment. [Procedure/backup rules](../user/studio-change.md).

## 13. Studio Odoo import packs

Use PA, an existing `plg-odooacc` checkout containing its real templates/catalogues, and a separate source/output workspace. Bind the checkout with `studio_odoo_bind`; inspect `studio_odoo_schema` and `studio_odoo_inventory` before generating anything.

The app does not provide an Odoo login/API connection or tax filing. It prepares CSV files for human review/import. Headers and catalogue codes must match; missing source values are blockers. PDFs may need a UTF-8 text companion for the source-reading path. Follow the [complete beginner Odoo sequence](../user/dummies-studio-odoo.md), including verification of copied catalogues and individual source values.

## 14. Administrator belt and MCP boundaries

The portable administrator feature needs its separate owner unlock, feature flag, encrypted brain, host allowlist and tools. Do not enable `SOL_STUDIO_ADMIN_FEATURE` alone and assume the belt is ready. Follow [full administrator setup](../user/admin-toolbelt-full-setup.md); this is not required for the four normal agents.

MCP wrappers exist under `src/sol_lite/mcp/` and import SDK interfaces, but the current manifest declares no `mcp` extra and the CLI has no MCP server-start subcommand. It needs developer dependency/API compatibility and explicit exposure/authorization wiring. Mark it **developer integration required**, not a beginner-ready connector. [MCP source guide](../development/mcp.md).

## 15. Record readiness and start using it

For each feature record: configured, blocked reason if any, actual check performed, actual result and evidence path. Do not include secrets. Required baseline checks are:

- Application version and dependency consistency checked.
- Ollama reachable; missing-model list empty.
- PA, Business, Docs and Engineer each complete an evidence-backed read-only workspace request.
- Each installed artifact format generates/validates; each desired renderer produces an inspected preview.
- Each connected service completes a separately approved narrow read.
- Voice capture and playback checked if used.
- Imported skills reviewed and assigned; background task completion inspected if used.

Maintainers can then run the repository's [battle-test runbook](../testing/battle-test-guide.md) deliberately. These docs do not claim those tests have been run. Continue to the [first-session walkthrough](first-session-walkthrough.md).
