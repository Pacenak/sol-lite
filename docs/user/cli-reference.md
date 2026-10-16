# CLI reference

Run from the repository root after install (`pip install -e .`) or via platform launchers. The console entry point is `sol-lite` (same as `python -m sol_lite`).

## Interactive runtime

| Command | Purpose |
|---|---|
| `sol-lite start` | Rich agent shell (default agent from user settings or `sol_pa`) |
| `sol-lite start --workspace <path>` | Bind the first session to a workspace directory |
| `sol-lite start --agent <id>` | Open as `sol_pa`, `sol_engineer`, `sol_business`, or `sol_docs` |
| `sol-lite start --verbose` | Verbose activity display (also toggled in-shell with `/verbose`) |

Terminal slash commands (`/help`, `/skills`, `/background`, `/listen`, `/speak`, `/flare`, …) are documented in [Commands](commands.md).

## Health and diagnostics

| Command | Purpose |
|---|---|
| `sol-lite doctor` | Local install, keyring pairing state, Jira connection state, voice readiness, Ollama endpoint |
| `sol-lite diagnose` | Pull Ollama tags and check configured profile models |
| `sol-lite version` | Print package version |
| `sol-lite voice-status` | Speech-to-text and text-to-speech probe lines |

`doctor` does **not** call SOL-Command or Jira over the network. Use `command-status` and `jira-status` for live probes.

## Quality gate

| Command | Purpose |
|---|---|
| `sol-lite battle-test` | Audit pack, preflight, compileall, pytest, ruff |
| `sol-lite battle-test --live --agent sol_engineer` | Adds one read-only Ollama tool-call smoke test |

Platform wrappers: `scripts/battle-test.bat` / `battle-test.command`.

## SOL-Command (optional)

| Command | Purpose |
|---|---|
| `sol-lite connect --command-url <url> --invite-code <code> [--name SOL-Lite]` | Pair; administrator must approve in Command |
| `sol-lite command-status` | Live `GET /api/lite/v1/status` |
| `sol-lite sync-skills` | Download sector skill packs to `data/state/skills/pending/sol-command/` |
| `sol-lite disconnect` | Remove local keyring credential |

See [Link SOL-Lite to SOL-Command (beginner)](dummies-command-link.md), [SOL-Command connection](../integrations/sol-command.md), and [SOL-Lite integration guide](../integrations/sol-lite.md).

## Google Workspace

| Command | Purpose |
|---|---|
| `sol-lite google-connect [--client-secrets <path>]` | OAuth; default secrets path from `SOL_GOOGLE_OAUTH_CLIENT_SECRETS` |
| `sol-lite google-status` | Keyring authorization present |
| `sol-lite google-disconnect` | Remove saved authorization |

## Jira Cloud

| Command | Purpose |
|---|---|
| `sol-lite jira-connect [--name …] [--base-url …] [--email …] [--projects …]` | Save site and project keys; token from `SOL_JIRA_API_TOKEN` or prompt |
| `sol-lite jira-status` | Probe saved sites (JSON) |
| `sol-lite jira-disconnect --name <connection>` | Remove connection and token |

## Configuration

Environment variables and YAML files: [Configuration](../architecture/configuration.md). Template: repository `.env.example`.
