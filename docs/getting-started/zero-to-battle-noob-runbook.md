# Zero-to-battle beginner runbook: terminal, admin, configuration and integrations

Read this chapter from top to bottom. It is the starting page for a new Windows operator. The instructions were checked by reading this repository; they have not been executed as part of writing these docs. Only follow a command when you reach its step. Do not paste the whole chapter into a terminal or into an agent chat.

## 0. Current checkout blockers — read before installing

Static inspection found these limits in this checkout:

- `scripts/preflight.py` requires exactly **39** `skills/*/SKILL.md` files, while this checkout contains **40**. Installer/preflight and the bundled battle gate are expected to stop with `PREFLIGHT FAIL: expected 39 built-in skills, found 40`. A maintainer must reconcile the intended catalogue and preflight contract. Do not delete a skill or change a test count just to pass.
- `battle-test` first validates `BUILD_MANIFEST.json` against payload filenames and SHA-256 hashes. These documentation changes add/change payload files. Until a maintainer reviews the intended payload and regenerates the manifest, the packaged gate can stop at the audit. See the [battle runbook](../testing/first-full-battle-run.md#3-understand-the-pack-audit-stop-condition).
- MCP wrappers are developer code with no declared `mcp` extra and no CLI server launcher. HTTP remote execution is an enum value but its transport raises `NotImplementedError`.
- Studio security agent module discovery currently derives `src/portable-stick/...` from the tool file, while the shipped portable tree is at repository-root `portable-stick/`. Owner unlock alone does not prove those tool calls will work. Treat a module-path failure as a product defect, not a missing admin permission.

The steps below describe the intended setup and how to record actual outcomes. **This checkout cannot honestly be called fully ready until its blocking contracts are resolved and the relevant checks are run.** Documentation is not a fix for those code/release issues.

## 1. Understand the three command locations

**Normal PowerShell** is your everyday terminal. It starts the application, installs Python packages into `.venv`, runs diagnostics and runs tests.

**Administrator PowerShell** is elevated Windows access. It is only for an identified operating-system installation/configuration step that needs it. It is not required to clone, edit YAML, create a virtual environment or run SOL-Lite. Do not run the whole agent session as Administrator to solve a tool denial.

**SOL-Lite chat** appears after the application banner. `/help`, `/settings` and normal prompts belong there. Windows commands such as `Set-Location` belong in PowerShell, not chat.

There is also a separate **Studio Admin agent**. Its feature/owner unlock is not the Windows administrator account and does not bypass SOL-Lite's permission engine.

## 2. Open and recognise each terminal

For normal PowerShell: open Start, type `Windows PowerShell`, then open it normally. The prompt commonly begins `PS C:\Users\...>`. That text is the prompt, not something to type.

For an elevated installation step only: Start, type `Windows PowerShell`, right-click it, choose **Run as administrator**, then accept the Windows consent prompt with an authorised account. A corporate machine may require IT credentials. Finish the specific OS step, close that elevated window, and reopen normal PowerShell.

If software installation asks for Windows consent, that is separate from an agent approval card. If you lack machine administrator rights, ask IT to install the required OS component; do not disable protections or use a different account to evade policy.

Terminal basics:

- Paste a single command, press Enter, wait for its prompt to return and read errors before the next line.
- Paths containing spaces need quotes: `Set-Location "C:\Users\YourName\My Folder"`.
- `Get-Location` prints your current folder. `Get-ChildItem` lists its contents.
- `#` starts a PowerShell comment. Text such as `YOUR_HOST` in an example must be replaced before running it.
- Ctrl+C interrupts the foreground terminal command. It does not undo completed work.
- A command's return to the prompt does not prove success. After a native program, `$LASTEXITCODE` normally contains its exit code; `0` means success for the documented checks.

You do not need virtual-environment activation for this guide. Explicit `.venv` interpreter paths avoid execution-policy and wrong-Python confusion. Do not change machine-wide PowerShell execution policy to follow these instructions.

## 3. Install the base system

Use the [complete base installation chapter](full-setup-first-run.md), sections 1–4, in this order:

1. Install Python 3.12, Git and Ollama. Runtime minimum is Python 3.11; 3.12 is the guide's selected version so Kokoro is eligible.
2. Reopen normal PowerShell and verify `py -3.12 --version`, `git --version` and `ollama --version`.
3. Ensure your account/network can access the corporate Git URL. A DNS/login failure needs repository/network access, not SOL-Lite configuration.
4. Clone under your own user folder and enter the checkout.
5. Run the common installer only when ready for package downloads, voice-model downloads and its attempted eSpeak-NG installation. It uses winget on Windows and may trigger OS-level installation requirements.
6. Stop at the current preflight mismatch described in section 0 and have a maintainer resolve it. Do not pretend installation reached its final success message.
7. Once the intended source is corrected, rerun the installer, download the four configured text models and inspect `diagnose` output.

The normal checkout location in the rest of this chapter is:

```powershell
Set-Location "$env:USERPROFILE\PLG_Ai_Lite"
Get-Location
Get-ChildItem
```

You should see `pyproject.toml`, `src`, `config`, `scripts`, `skills` and `docs`. No required workflow depends on a developer's `E:` drive.

## 4. Learn how to edit configuration files

Close SOL-Lite before editing configuration directly. Open files from normal PowerShell with Notepad:

```powershell
notepad .\config\models.yaml
```

After editing, save with Ctrl+S and close Notepad. Keep `.yaml` or `.env` as the actual extension, not `.txt`. In File Explorer, enable **File name extensions** to check. Use UTF-8; for newly saved files use the editor's UTF-8 option. YAML indentation uses spaces, not tabs. Preserve surrounding sections and quote paths/URLs when copying examples.

### Minimum `.env`

No variables are required. Leave `.env` absent for the smallest setup. If you need overrides, open the exact filename:

```powershell
notepad .env
```

Accept creation only if the file does not exist. For a beginner local setup, the following optional values are understood by source:

```dotenv
SOL_WORKSPACE_ROOT=./workspace # Default working root.
SOL_DATA_ROOT=./data # Default state root; not every workflow relocates with this value.
SOL_OLLAMA_URL=http://127.0.0.1:11434 # Model service running on this computer.
SOL_SEARXNG_ENABLED=false # Leave search off until a real service is configured.
```

Do not paste all optional credential names as blank required settings. Do not put `SOL_INSTANCE_ID` or `SOL_INSTANCE_KEY` here; bootstrap rejects them. A terminal environment variable already set by the launcher/shell can override `.env`; restart in a fresh shell when diagnosing a stale override.

A temporary override in PowerShell looks like this and lasts only in that shell and its child processes:

```powershell
$env:SOL_WORKSPACE_ROOT = "$env:USERPROFILE\SOL-Lite-Practice"
```

To remove only that process override:

```powershell
Remove-Item Env:SOL_WORKSPACE_ROOT -ErrorAction SilentlyContinue
```

That removes an environment entry, not a file. It does not edit `.env` or Windows' persistent environment settings. Do not use `setx` for the beginner path.

### Per-user settings

In chat, `/settings` is the simplest editor. Review the category labels in [full configuration](full-feature-configuration.md#3-configure-the-four-standard-agents). Models/agents generally need a restart to recompose; some display/search settings apply immediately.

To edit an existing Windows settings file directly:

```powershell
notepad "$env:APPDATA\SOL-Lite\settings.yaml"
```

If the folder does not exist yet, use `/settings` to save a preference first. Do not overwrite existing settings with a template. Use the nested user-settings example from [full feature configuration](full-feature-configuration.md#3-configure-the-four-standard-agents) only when you understand which mapping you are merging.

Precedence is repository YAML, allowed user settings, supported environment overrides, then applicable start flags. Per-user settings cannot replace permissions. Model names are YAML/profile values, not invented environment names such as `SOL_FAST_MODEL`.

## 5. Finish all four agents and package extras

Follow [source update and extras](full-feature-configuration.md#1-update-the-source-without-losing-work). Never pull over unreviewed local work. The installer supplies `dev,voice`; explicitly adding `artifacts,google` covers the other declared extras:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[artifacts,google]"
.\.venv\Scripts\python.exe -m pip check
```

Keep PA=`fast`, Business/Docs=`reviewer`, Engineer=`engineer` initially. Inspect the effective settings, configured model names and `ollama list`. A model name or capability label is not proof of actual tool-call competence. Verify each agent in the first session and battle run.

To refresh built-in agents/skills, update the intended source release and repair its environment. Imported external skills use their own discover/review/update lifecycle; do not reinstall every external source blindly. The currently mismatched skill count is a source-contract issue, not something a beginner should repair by removing a skill folder.

## 6. Connect each optional integration in order

For every service, write down its prerequisite, the configuration you changed, the actual check and the outcome. A token saved or status command completed is not the same as a successful real operation. Use test accounts/projects and non-sensitive sample data for the first battle.

### A. Artifact authoring and rendering

Install the `artifacts` extra above. Install LibreOffice using its official desktop installer. Install Node.js LTS, reopen normal PowerShell, then run the Mermaid CLI install from [artifact setup](full-feature-configuration.md#5-artifact-creation-and-exports). OS installers may ask for consent; package generation and the agent do not need an elevated terminal.

Check authoring packages and renderer availability with `artifact_dependencies`, then create/validate/render fresh DOCX, PPTX, XLSX and Mermaid outputs. Open the files and previews. Formula text alone is not calculated-value evidence. The [battle chapter](../testing/first-full-battle-run.md) gives a strict renderer check.

### B. Voice

Run `voice-status` through the `.venv` interpreter. Use `/settings`, `V` to inspect providers. Grant microphone access under Windows privacy settings if necessary. Test `/listen` with harmless words and `/speak` with a short response. Read the toggle state: invoking it can turn speech off as well as on.

If local TTS needs eSpeak-NG, arrange its install through the documented installer/IT, then reopen the terminal and recheck. A voice-weight download failure is not fixed by granting the agent Administrator rights. Local and hosted endpoint settings are covered in [voice configuration](full-feature-configuration.md#6-local-voice).

### C. SearXNG

This repository is a **client**, not a SearXNG server deployment. Obtain from the service administrator: a reachable base URL, JSON search enabled under `search.formats`, and network access from this PC. An interactive login page or an unsupported authentication layer is not a working search API.

Set `SOL_SEARXNG_URL` and `SOL_SEARXNG_ENABLED=true` in `.env`, verify the `/search?...&format=json` request in [search configuration](full-feature-configuration.md#7-private-web-search-searxng), restart and run the search starter prompt. Do not copy a private IP from a developer's example and assume it exists on your network. If no service has been provided, record `BLOCKED: SearXNG endpoint not provisioned`.

### D. Gmail and Google Calendar

The Google extra is required first. A Google account administrator must allow a Google Cloud project, enable Gmail API and Google Calendar API, configure OAuth consent for your account, and create a **Desktop app** OAuth client. If the app is in testing, your account must be permitted as a test user. Download its JSON outside the Git checkout.

Use `google-connect --client-secrets` with that real path, complete browser consent, then run `google-status`. Close/restart chat and use PA for the first narrow approved Gmail/calendar read. Source requests Gmail read/send and owned-calendar event scopes. No send/meeting is required to prove a connection. See the [exact commands](full-feature-configuration.md#8-gmail-and-google-calendar).

If access is blocked by Google consent/account policy, have the account/project administrator resolve it; do not paste credentials into chat. OS keyring storage is used. `google-disconnect` removes local saved credentials. Google account-side app access/revocation is a separate account-management action.

### E. Jira Cloud

Get the actual Jira site URL, account email, API token and permitted test project keys from your Jira administrator. Run `jira-connect` interactively so the token is entered at its prompt rather than stored in a copied command or transcript. Run `jira-status`, restart chat and ask PA/Engineer for a read of one granted issue.

Where needed, use the Jira workspace binding tools to select the connection/project. Do not guess cross-site issue IDs. Reads, writes and project restrictions remain gated. `jira-disconnect --name NAME` removes a local connection; provider-side token revocation is separate. [Jira sequence](full-feature-configuration.md#9-jira-cloud).

### F. SOL-Command

A Command administrator must operate the server. Ask them for the correct HTTPS base URL, a **Lite** invite, intended sectors and approval of the pending `sol-lite` instance. Do not reuse an Outpost key. Run `connect`, wait for the administrator, then run `command-status`.

Restart chat before testing PA's sector tools. `sync-skills` downloads to pending review; inspect/import individually afterwards. Jarvis needs its own grant and remains a pending proposal. The disabled bridge configuration is unrelated to pairing. Follow the [admin/operator chapter](../user/dummies-command-link.md) and [configuration sequence](full-feature-configuration.md#10-sol-command-pairing-and-skill-packs). No local administrator terminal can approve the remote Command instance.

### G. Host Git and GitHub-compatible PR workflows

Use the real repository as workspace. Set up Git hosting credentials as your normal user through your organisation's documented authentication. Do not place a token in a remote URL. Confirm read-only status/remotes before granting remote trust.

GitHub PR tools need `gh` installed and authenticated to the correct GitHub/GitHub Enterprise host. A corporate Git server is not necessarily GitHub-compatible. Configure the real host using `gh auth login`, then check `gh auth status`. Do not publish a PR or push just to prove read access. [Git and hosting steps](full-feature-configuration.md#11-git-remotes-and-pull-requests).

### H. SSH lab hosts

Windows OpenSSH Client is optional OS software. If `ssh -V` is unavailable, have Windows/IT install **OpenSSH Client** using Windows' Optional Features interface, accepting administrator consent only for that OS step. Start a new normal terminal afterwards.

Obtain the lab host, user, authentication method and trusted host-key fingerprint from its administrator. Follow their normal OpenSSH setup in your user profile. Do not accept an unknown fingerprint blindly. Establish SSH access outside SOL-Lite first, then copy the actual host details into `config/remote-nodes.yaml` using the [SSH example](full-feature-configuration.md#12-remote-hosts-and-procedure-manuals). Set `environment: lab` only for a real lab target you are permitted to change.

Restart, list configured nodes and approve one harmless read such as `uname`. No password/private key belongs in YAML or tool arguments. Missing credentials, DNS or firewall access are host prerequisites, not agent bugs.

### I. PowerShell remoting

The target Windows host must already permit your identity to use its Windows remoting service through the intended network/domain policy. Have the host administrator configure the service, authentication and firewall through the organisation's runbook. This client invokes `Invoke-Command -ComputerName`; it does not provision a remoting server or supply a password.

Use `transport: powershell` only after a harmless `Invoke-Command` read works as your normal user outside SOL-Lite. Remote remoting setup can require elevation **on the target**; elevating Lite locally is not a substitute. Configure a named node, restart and inspect the intended target. HTTP API remote transport is currently unimplemented.

### J. Procedures, workspace memory and Studio Odoo

Put a procedure manual inside the workspace. `/follow relative-path.md` is a dry inspection. Loading a manual does not authorize execution. PA can load/status/acknowledge; Engineer also has advance and Studio change tools. [Studio workflow](../user/studio-change.md).

Workspace notes use `workspace_notes_write/read` and are saved outside the project under `data/memory/<workspace_id>/notes.md` by default. Chat sessions themselves are not restored after quit. Use explicit handoff files and verify saved notes rather than assuming the whole conversation is permanent.

For Odoo, get a valid `plg-odooacc` checkout with templates and initialise a separate import workspace as described in the [beginner Odoo chapter](../user/dummies-studio-odoo.md). PA must bind the supplied root and inspect schema/source inventory before copying catalogues or writing CSVs. It prepares import files only; it does not connect to Odoo or submit returns.

### K. MCP, scheduling and disabled integration flags

MCP needs developer implementation/dependency compatibility and explicit exposure/authorization wiring; see [MCP](../development/mcp.md). It is not enabled by installing an undefined extra.

A background task is not an external scheduler. `schedules.yaml` is disabled by default, and the existence of schedule/NAS/bridge/platform settings does not prove an end-to-end operational feature. Do not enable all switches to claim “all features”. Mark unavailable paths unsupported/developer-required until implemented and verified.

## 7. Studio Admin feature — separate from Windows elevation

Only the authorised lab owner should follow this part. The four normal agents work without it. For a USB belt, encryption, volumes, hardware and boot personalities, use the [complete portable setup](../user/admin-toolbelt-full-setup.md); do not partition a disk as part of a beginner application install.

Owner-gated setup needs all of:

1. The Studio Admin feature flag.
2. `SOL_STUDIO_OWNER` enabled in the launching process.
3. An owner unlock file containing the required phrase.
4. A matching `owner_id` when `SOL_STUDIO_OWNER_ID` is supplied.
5. A real `hosts.allow` for security checks; owner unlock is not permission to target arbitrary addresses.

For an owner-controlled **non-portable local lab**, a concrete layout is:

```text
%USERPROFILE%\SOL-Lite-Lab\
  workspace\
  sec\
    I_OWN_THIS_LAB
    hosts.allow
```

Create folders in normal PowerShell:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SOL-Lite-Lab\workspace"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\SOL-Lite-Lab\sec"
notepad "$env:USERPROFILE\SOL-Lite-Lab\sec\I_OWN_THIS_LAB"
```

The unlock file contents, with your actual chosen owner handle:

```text
I OWN THIS LAB
owner_id: YOUR_OWNER_HANDLE
```

Save it with no `.txt` extension. Create `hosts.allow` in the same `sec` folder using Notepad. For the first local-only fixture its entire content can be `127.0.0.1`. That does not promise a listening service on any port. Never add a host you do not own or have permission to test.

After the code blockers have been resolved, set process-only values in normal PowerShell before launch:

```powershell
$env:SOL_STUDIO_ADMIN_FEATURE = '1'
$env:SOL_STUDIO_OWNER = '1'
$env:SOL_STUDIO_OWNER_ID = 'YOUR_OWNER_HANDLE'
$env:SOL_WORKSPACE_ROOT = "$env:USERPROFILE\SOL-Lite-Lab\workspace"
.\.venv\Scripts\python.exe -m sol_lite start --workspace "$env:USERPROFILE\SOL-Lite-Lab\workspace"
```

Replace the handle consistently. The root override matters because the registry evaluates unlock during bootstrap, before the interactive workspace selection. In chat run `/agents`, then `/use sol_studio_admin` if listed, and request only `studio_owner_status` initially. No Windows Administrator window is required for that owner gate.

Current module-path defects noted in section 0 can still block SecCheck/lite-pen even with this layout. Record that, do not copy source modules into guessed locations to force a pass. These tools write reports to the workspace, require allowlisted targets and do not supply exploits.

Close the shell afterwards. Clear owner flags by closing that PowerShell window, then use a fresh normal terminal for the ordinary battle. Do not save owner unlocks in public repositories, reports or screenshots.

## 8. Do the first session, then the full battle

First follow [first-session walkthrough](first-session-walkthrough.md): inspect the practice input with all four agents, create one deliberate output, check background work and save a handoff.

Then follow [first full battle run](../testing/first-full-battle-run.md). It gives exact disposable fixtures, logs, commands, live smoke for each agent, skill coverage, rejection tests, artifact acceptance, integration checks and a completion record.

Use [starter prompt packs](../user/starter-prompt-packs.md) for ordinary work. Keep unavailable features marked blocked, skipped checks marked not run, and source/release defects marked fail. Never replace missing evidence with an “all working” conclusion.

## 9. If a beginner step fails

- **Program not recognised:** finish installing that program and reopen the terminal; check the version command before proceeding.
- **`Activate.ps1` blocked:** activation is unnecessary; use the explicit `.venv` interpreter shown here.
- **`Configuration file not found` or YAML errors:** confirm the full checkout and correct filename/space indentation; restore only the intended configuration from your reviewed backup.
- **Connection refused/model missing:** check Ollama and its exact model tags; do not change Windows administrator permissions.
- **Keyring failure:** preserve the actual error; use the normal account with a working OS credential store. Do not fall back to pasting tokens into model context.
- **Approval denied/blocked command:** inspect the scope and request; do not enable every permission or elevate the whole agent.
- **39/40 skills or manifest mismatch:** use the documented maintainer stop condition, not repeated package installation.

## 10. macOS operators

Use the [macOS base setup](full-setup-first-run.md#macos-equivalent), then the same feature/first-session chapters. Terminal is under Applications → Utilities. Use normal user access; an OS installer may request administrator consent. `sudo` is not required for ordinary `.venv` package installation or agent use. Use `.venv/bin/python` for app commands and `export NAME=value` / `unset NAME` for process environment overrides. Windows remoting service setup remains a target-host responsibility. The [battle runbook](../testing/first-full-battle-run.md) includes macOS fixture and logging equivalents.
