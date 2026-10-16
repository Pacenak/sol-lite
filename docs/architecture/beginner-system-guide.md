# SOL-Lite: beginner system guide

For the v0.2.6 tree, checked through static code reading. This is not evidence of live installation, service health or model quality. Start with [setup](../getting-started/full-setup-first-run.md), then the [user guide](../user/beginner-user-guide.md).

## What each piece does

Python runs the program. The terminal collects messages and displays activity. A session holds an agent, workspace and recent conversation. An agent supplies a role prompt and allowed tools. Ollama supplies model responses. Tools perform actual operations. Permission checks and guards constrain those operations. Skills add instructions. Particular logs and state files record evidence and settings.

A model's proposed action is not an executed action. The runtime accepts native structured Ollama tool calls; ordinary text resembling JSON or a tool invocation is not executed. Review tool results and files before accepting completion claims.

## Startup in order

1. `sol-lite` or `python -m sol_lite` enters `src/sol_lite/app.py`. Interactive mode requires `start`.
2. `bootstrap.py` resolves the checkout, loads `.env` when present, and reads required YAML configuration.
3. Allowed per-user settings merge with defaults. Supported environment variables override particular roots/endpoints. CLI flags select initial agent, workspace and verbose display.
4. Bootstrap composes models, agents, permissions, tools, skills, logging and optional clients.
5. Runtime startup creates configured workspace, data and logging directories.
6. The shell selects/registers an existing workspace, creates a session and prints the banner. Messages can then invoke models and tools.

A banner is not an end-to-end check. Missing models, insufficient memory, optional libraries and private API errors may surface only when used.

## File and folder map

- `pyproject.toml`: runtime minimum, dependencies, extras and console entry point. Dependencies have lower bounds; this is not an exactly locked environment.
- `requirements.txt`: another package list including development tools. The common installer instead uses `pip install -e .[dev,voice]` from the manifest.
- `src/sol_lite/`: implementation. `app.py` dispatches CLI subcommands; `agents/shell.py` dispatches slash commands.
- `config/`: application, model, agent, permission and logging defaults. Keep required files with the checkout even when a feature is disabled.
- `prompts/`, agent `prompt.md` files and `skills/`: runtime guidance.
- `.venv/`: replaceable installed Python environment, not your project backup.
- `workspace/`: default working folder. Actual selected workspaces can be elsewhere.
- `data/`: default local state, memory-related folders, cache and faults. A `rag` folder or embedding model profile does not establish automatic document indexing.
- `data/state/workspaces.json`: remembered workspace metadata.
- `data/state/voice.json`: voice settings. Voice downloads also use cache directories.
- `data/state/procedures/`: saved procedure state.
- `data/state/backups/`: Studio workflow backups.
- `data/state/skills/pending/sol-command/`: staged skills awaiting review, not automatic activation.
- `data/faults/faults.json`: bootstrap's fault log path.
- `logs/sol-lite-audit.jsonl`: default audit path. Application log settings are separate.
- `docs/`: instructions, not executable feature switches.

Some paths are explicitly rooted in the checkout. Do not assume `SOL_DATA_ROOT` relocates every fault, backup or integration file: inspect the relevant workflow before moving state.

Windows user preferences normally live at `%APPDATA%\SOL-Lite\settings.yaml`; macOS uses `~/Library/Application Support/SOL-Lite/settings.yaml`. `SOL_LITE_SETTINGS_FILE` can override this. Credentials live in the OS keyring, not these YAML settings.

## Models, ports and infrastructure

Default Ollama endpoint: `http://127.0.0.1:11434`. The Python Ollama library is a client: installing it does not install/start the server or download text models.

Profiles choose PA, engineering, reviewer and embedding models. User overrides can change them. An explicitly configured network provider receives requests at its configured endpoint; local-first describes defaults rather than a guarantee that every possible setup keeps all content local.

No PostgreSQL or Redis server is required by normal bootstrap. SearXNG is disabled by default. Remote nodes are explicitly configured rather than automatically discovered. SOL-Command uses a separate optional remote API. The disabled `bridge` block with port `8787` is not the pairing switch or a browser UI.

## Permissions and trust

`config/permissions.yaml` controls scopes. User settings cannot replace it. Filesystem containment, role paths, command classification, exact approvals and integration restrictions add checks.

With write permission enabled, role-path file writes can run without a popup. Private-account reads and network activity have separate gates. Trusting Git remotes changes repeated remote approvals for that checkout. Skills cannot grant permissions. Approval does not make destructive or nested-shell commands valid.

Studio changes distinguish Git-tracked files, backed-up untracked files, quarantine and remote lab/production restrictions. That workflow is not a promise that all operations are transactional or automatically reversible. See [Studio changes](../user/studio-change.md).

## Persistence and its limits

Workspace registrations, user settings and particular state files persist. `SessionManager` keeps sessions in memory; conversation context retains only the last six turn pairs. There is no full chat-restoration promise after quitting.

Background tasks use a process-local thread pool, not a durable queue or external scheduler. Do not assume tasks survive shutdown or provide automatic monitoring.

Account credentials persist in the OS keyring. Copying the source does not copy authenticated access. Disconnecting locally from Command does not revoke its remote instance; that requires administrator action on Command.

## Installation versus daily operation

The common installer creates/reuses `.venv`, installs dependencies, attempts voice provisioning, performs preflight/Doctor checks and writes install metadata. It can invoke external software installers. Normal launch uses the installed environment without reinstalling it.

Doctor checks runtime and stored integration state and includes Ollama diagnostics; it does not prove a Jira or Command API action works. `jira-status` and `command-status` are their respective live probes. `diagnose` lists Ollama availability and missing models; its overall success alone does not prove every model exists.

Battle tests are maintainer acceptance work and can execute code or optional live model requests. They are not a prerequisite for a beginner's first chat. An installer metadata version is not more authoritative than package/source/configuration versions checked by preflight.

## Feature setup and next reading

The [user guide](../user/beginner-user-guide.md) covers chat, skills, tasks, voice, artifacts and each optional integration. Use [configuration](configuration.md) for supported variables, [CLI reference](../user/cli-reference.md) for shell commands, [security](../security/security-model.md) for policy, and [debugging](../debugging/debugging-overview.md) for errors.

Back up actual workspaces, configuration, required state and user preferences before upgrades or repairs. Keep credentials and private state out of public source control. Preserve the complete checkout and reinstall the environment on a new machine.
