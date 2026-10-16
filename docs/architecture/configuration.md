# Configuration

SOL-Lite merges configuration from several layers. Later layers override earlier ones where merge rules allow. **Permission policy is not overridable from user settings.**

## Layer order

1. **Repository YAML** under `config/` (shipped defaults).
2. **Per-user settings** outside the repository (`settings.yaml`), merged at startup for allowed sections only.
3. **Environment variables** for a small set of roots and integrations (see below).
4. **CLI flags** on `sol-lite start` (`--workspace`, `--agent`, `--verbose`).

Bootstrap loads `.env` from the repository root when present (`load_dotenv` in `bootstrap.load_config`).

## Repository files (`config/`)

| File | Purpose |
|---|---|
| `sol-lite.yaml` | Application name/version, runtime limits, workspace and data roots, skills discovery roots, logging, background tasks, platform integration toggles, optional local `bridge` listener |
| `permissions.yaml` | Filesystem, terminal, network, repository, studio, and integration scopes — **not** copied into user settings |
| `agents.yaml` | Agent ids, prompts, model profiles, tool allowlists |
| `models.yaml` | Ollama provider endpoint and named profiles (`fast`, `engineer`, `reviewer`, `embedding`) |
| `schedules.yaml` | Scheduled task definitions |
| `logging.yaml` | Log level, console/file sinks |
| `searxng.yaml` | Private SearXNG base URL and search defaults |
| `remote-nodes.yaml` | Optional SSH lab/production hosts for `remote_list_nodes` / `remote_execute` (no secrets in file) |
| `skill-sources.yaml` | Declared external skill source metadata |

Voice preferences are **not** in `config/`. They live in `data/state/voice.json` (created by install / `voice-status` / `/speak`).

Procedure checklist state lives in `data/state/procedures/` keyed by workspace path hash.

Integration credentials (SOL-Command, Google, Jira, `plg-studio` secret names) live in the **OS keyring**, not in YAML or `.env`.

## Per-user settings

Path (unless overridden):

- Windows: `%APPDATA%\SOL-Lite\settings.yaml`
- macOS: `~/Library/Application Support/SOL-Lite/settings.yaml`
- Linux: `~/.config/sol-lite/settings.yaml`

Override the path with `SOL_LITE_SETTINGS_FILE`.

Allowed sections include `general`, `runtime`, `workspace`, `data`, `logging`, `background`, `macos`, `windows`, `nas`, `bridge`, `models`, `agents`, `searxng`, and `display`. Settings UI and `/` commands may persist changes here. Sections such as `permissions`, `security`, and `credentials` are rejected.

## Environment variables

Variables the runtime **reads today** (see `.env.example` for copy-paste templates):

| Variable | Effect |
|---|---|
| `SOL_WORKSPACE_ROOT` | Overrides `workspace.root` in `sol-lite.yaml` |
| `SOL_DATA_ROOT` | Overrides `data.root` |
| `SOL_OLLAMA_URL` | Ollama HTTP base URL; overrides `models.yaml` `provider.endpoint` |
| `SOL_SEARXNG_URL` | Overrides SearXNG base URL |
| `SOL_SEARXNG_ENABLED` | `true`/`1`/`yes`/`on` enables search integration |
| `SOL_COMMAND_URL` | Optional Command host; must match paired host in keyring |
| `SOL_GOOGLE_OAUTH_CLIENT_SECRETS` | Path to OAuth client JSON for `sol-lite google-connect` |
| `SOL_JIRA_API_TOKEN` | Token for non-interactive `sol-lite jira-connect` |
| `SOL_LITE_SETTINGS_FILE` | Alternate user `settings.yaml` path |
| `SOL_STUDIO_ADMIN_FEATURE` | `1` turns on the **admin-only** studio tool-belt feature (`features.studio_admin`; default off) |
| `SOL_STUDIO_OWNER` | `1`/`true` personal unlock half of the admin gate (stick launcher sets when unlock file exists) |
| `SOL_STUDIO_OWNER_ID` | Optional; must match `owner_id:` in unlock / `I_OWN_THIS_LAB` so admin unlock binds to you |

**Rejected at bootstrap:** `SOL_INSTANCE_ID` and `SOL_INSTANCE_KEY` (pair with `sol-lite connect`; secrets stay in the keyring).

**Studio command placeholders:** Any `{{NAME}}` in an approved checklist command can resolve from the keyring (`plg-studio` provider) or from an environment variable with the same name (see `security/secrets.py`).

**Voice hosted endpoints:** If `data/state/voice.json` defines an endpoint with `api_key_env`, set that variable name in the environment before `/listen` or `/speak`.

**LibreOffice discovery (artifacts):** Uses `PROGRAMFILES` / `PROGRAMFILES(X86)` on Windows when searching for `soffice.exe`.

**CI / tests only:** `SOL_RUN_OLLAMA_TESTS`, `SOL_REQUIRE_ARTIFACT_RENDERERS`, `SOL_ARTIFACT_ACCEPTANCE_OUTPUT`.

### Not environment-driven

These appear in older examples or legacy scripts but are **not** read by current `src/sol_lite` bootstrap:

- `SOL_LITE_ENV`, `SOL_LOG_LEVEL`, `SOL_FAST_MODEL`, `SOL_ENGINEER_MODEL`, `SOL_REVIEWER_MODEL`, `SOL_EMBEDDING_MODEL`
- `SOL_REQUIRE_APPROVAL_FOR_WRITES`, `SOL_REQUIRE_APPROVAL_FOR_SHELL`
- `OLLAMA_HEARTBEAT_*`, `OLLAMA_SLOW_THRESHOLD_*`, `OLLAMA_STALL_THRESHOLD_*`, `OLLAMA_REPEAT_TOOL_THRESHOLD`, `OLLAMA_MAX_TOOL_ROUNDS`

Use `config/sol-lite.yaml` (`runtime.*`), `config/logging.yaml`, `config/models.yaml`, and `config/permissions.yaml` instead.

## Related docs

- [CLI reference](../user/cli-reference.md) — `sol-lite` subcommands
- [Studio change gate](../user/studio-change.md) — `remote-nodes.yaml`, procedures, studio tools
- [Integrations](../integrations/sol-lite.md) — SearXNG, Google, Jira, SOL-Command, Studio Odoo
- [MCP developer integration](../development/mcp.md) — source wrappers exist; the current manifest does not define an `mcp` extra or beginner launch command.
