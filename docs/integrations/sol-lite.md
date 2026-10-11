# SOL-Lite integration guide

SOL-Lite is a local-first multi-agent runtime for Windows and macOS. This guide is for someone installing it and deciding whether to pair it with SOL-Command.

SOL-Lite runs completely without SOL-Command. Pairing is optional. It does not copy Lite workspaces, local memory, sessions, or credentials into Command.

## What you need

| Piece | Required for standalone use? | Role |
|---|---|---|
| Python 3.11+ | Yes | Runtime |
| Git | Recommended | Repository workflows and external skill sources |
| Ollama | Yes, for agents | Local model provider |
| SOL-Command | No | Optional shared sectors, pack skills, and Jarvis proposals |
| SearXNG, Google, Jira | No | Separate optional integrations. None of them is the Command link |

The install and first-run sequence is in [Full setup and first run](../getting-started/full-setup-first-run.md). Platform notes are in [Windows](../getting-started/windows.md) and [macOS](../getting-started/macos.md).

After setup, commands below assume the project directory. The console script is `sol-lite`.

```powershell
.\.venv\Scripts\sol-lite.exe doctor
```

```bash
.venv/bin/sol-lite doctor
```

A first install that has never paired prints `SOL-Command: not paired (standalone)`. That is the normal standalone state. `doctor` checks the local install. It does not call Command.

## Standalone daily use

Start SOL-Lite from the project launcher or `sol-lite`. The first session without `--workspace` asks for a recent workspace or a new path. Each session keeps its own workspace. Workspace paths are contained; one session cannot read another session's workspace by crossing that boundary.

The terminal commands for local work are:

```text
/help
/agents
/use <agent>
/new
/workspace
/workspaces
/sessions
/skills list
/skills discover <source>
/skills import <source>
/skills update <skill>
/skills assign <skill> <agent>
/skills remove <skill>
/background <prompt>
/tasks
/tasks cancel <id>
/status
/verbose
/debug
/normal
/tools
/doctor
/quit
```

Agents:

- `sol_pa` — coordination, planning, research, scheduling, and delegation.
- `sol_business` — business operations, projects, reporting, and analysis.
- `sol_docs` — documents, presentations, spreadsheets, diagrams, and extraction.
- `sol_engineer` — software engineering, debugging, testing, Git, and technical operations.

Built-in skills install with the product. External skills stay inactive until `/skills discover` and `/skills import`. Skills do not grant tool permissions. Artifact setup is in [Artifacts](../user/artifacts.md). Approvals, sessions, and workspaces are in the [user guide](../user/commands.md).

`config/sol-lite.yaml` has a `bridge` block (`enabled`, `listen_host`, `listen_port`). It defaults to disabled. That block is a local listener switch. It is not the SOL-Command pairing switch. Leave it off unless you have a reason to enable the listener. If it is on, `sol-lite doctor` warns that pairing is separate and points at `sol-lite command-status`.

## Optional integrations that are not Command

These work on an unpaired Lite install:

- Private web search through SearXNG. See [SearXNG](searxng.md).
- Gmail and Calendar for the PA. See [Google Workspace](google-workspace.md). Connect with `sol-lite google-connect`.
- Jira Cloud boards for the PA and Engineer. See [Jira](jira.md). Connect with `sol-lite jira-connect`.

Each of those stores its own credential in the operating system keyring. None of them creates a SOL-Command instance.

## Optional SOL-Command link

Pair when this Lite machine should read Command sectors assigned to it, download those sectors' applied skill packs for local review, or submit a Jarvis proposal. Command remains the authority for instance identity, sector assignment, and Jarvis grants. Lite keeps local approval, audit, sessions, and workspaces.

Use HTTPS for any Command host that is not loopback. HTTP is accepted only for `localhost`, `127.0.0.1`, or `::1`. The URL is a base URL: no user, password, query, or fragment.

### Pair

1. In SOL-Command, create an invite for the sectors this Lite instance should use.
2. On the Lite machine, run:

```powershell
.\.venv\Scripts\sol-lite.exe connect --command-url https://sol-command.example --invite-code YOUR_INVITE
```

```bash
.venv/bin/sol-lite connect --command-url https://sol-command.example --invite-code YOUR_INVITE
```

`--name` defaults to `SOL-Lite`. The command registers `client_type: sol-lite`, then waits for an administrator to approve the pending instance. Approval has to happen in Command. Lite cannot approve itself.

3. After approval, Lite claims the instance once. The command prints the instance id and assigned sectors. The instance id and API key are stored in the OS keyring under the SOL-Lite `sol-command` credential. They are not written to `.env`, repository settings, logs, or model context.
4. Check the live connection:

```text
sol-lite command-status
```

That call hits `GET /api/lite/v1/status` with `X-Sol-Instance-Id` and `X-Sol-Instance-Key`. A successful body has `ok`, `instance_id`, `sectors`, and `lite_access`. It does not include the API key. `sol-lite doctor` only reports whether a credential is saved (`paired` or `not paired (standalone)`). Use `command-status` when you need to know Command is reachable.

`SOL_COMMAND_URL` may name the host, and it must match the host stored at pairing. `SOL_INSTANCE_ID` and `SOL_INSTANCE_KEY` are rejected. Secrets come from the keyring only.

### What the paired PA can do

Only `sol_pa` receives the Command tools. It uses them when the request is about SOL-Command, shared memory, a sector, or Jarvis. The Engineer, Docs, and Business agents do not get these tools.

| Tool | Command route | Effect |
|---|---|---|
| `sol_command_status` | `GET /api/lite/v1/status` | Paired instance id, assigned sectors, and Lite grants |
| `sol_shared_memories` | `GET /api/lite/v1/sectors/{sector_id}/memories` | Approved memories for one assigned sector |
| `sol_shared_rag_search` | `GET /api/lite/v1/sectors/{sector_id}/rag/search` | Keyword search of that sector's registered RAG metadata |
| `sol_jarvis_propose` | `POST /api/lite/v1/sectors/{sector_id}/jarvis/proposals` | Submit a proposal and leave it pending |

Every one of those calls passes Lite's network permission and approval policy. Command checks the instance key and current sector assignment on every request. A sector that is not assigned is denied, even if the caller supplies its id. Memory reads exclude entries marked proposed. RAG search here is metadata keyword search, not a full vector retrieval. Results stay remote. Lite does not copy them into its local memory store.

If Command is down, revoked the instance, or changed sectors, the remote tool returns an error. Local tools, agents, workspaces, models, and skills keep working. Lite does not substitute local data for a failed remote call.

### Skill packs

```text
sol-lite sync-skills
```

This posts to `/api/hub/sync/packs` with the paired instance id and key. Command returns applied pack bodies for the instance's assigned sectors only. Lite writes them under:

```text
data/state/skills/pending/sol-command/<sector-slug>/<skill-slug>/<content-hash>/SKILL.md
```

Nothing in that tree is activated. Review each skill, then `/skills discover <path>` and `/skills import <skill>`. A later sync with different content writes a new hash directory. Installed skills are not overwritten or deleted.

### Jarvis proposals

Jarvis submission stays off until a Command administrator grants that instance. The grant is:

```http
PATCH /api/hub/instances/{instance_id}/lite-access
Content-Type: application/json

{"jarvis_propose": true, "jarvis_domains": ["skills", "code_fix"]}
```

Allowed domains are `meal_plans`, `fitness_plans`, `skills`, `memories`, `home_pa`, and `code_fix`. Command also requires its Jarvis persona policy to allow that domain. Lite records the proposal as the Lite instance and receives a pending ticket with `manual_required: true`. Lite cannot approve or apply the ticket.

### Disconnect and revoke

On the Lite machine:

```text
sol-lite disconnect
```

That deletes the local keyring entry. It does not revoke the instance on Command. A Command administrator removes it with `DELETE /api/hub/instances/{instance_id}`. After that removal, `sol-lite command-status` and the Command tools fail. Local Lite use continues. Pair again with `sol-lite connect` if the machine should rejoin.

## Link limits

- There is no background sync. Status, memories, RAG, skill download, and Jarvis run when a command or the PA calls them.
- Shared memories and RAG are read-only on this link.
- Skill sync stages packs for review. It does not install SOL's whole skill library.
- Jarvis submits allowlisted proposals. It does not monitor Jarvis or approve changes.
- An Outpost instance key cannot call `/api/lite/v1`. The instance has to be paired as `sol-lite`. A claim whose `client_type` does not match the approved instance is rejected, and the credential is not issued.
- Treat the Command host as a system you operate. Confirm its address and who can approve instances before using it on a LAN or VPN.

## Standalone checklist

1. `sol-lite doctor` completes and shows `SOL-Command: not paired (standalone)` when you have not paired.
2. A session opens on a chosen workspace and `/agents` lists the four agents.
3. `/skills list` shows the built-in skills.
4. SearXNG, Google, or Jira, if you use them, connect with their own commands and still work while Command is unpaired.

## Paired checklist

1. `sol-lite connect` finishes only after a Command administrator approves the pending SOL-Lite instance.
2. `sol-lite command-status` returns the instance id and the sectors from that approval, and the output has no API key.
3. A memory or RAG request for an unassigned sector is denied.
4. `sol-lite sync-skills` writes pending `SKILL.md` files and does not install them.
5. `sol_jarvis_propose` is denied until the administrator sets `lite-access`, and a successful call stays pending.
6. `sol-lite disconnect` removes the local credential. After the administrator deletes the instance, later status calls fail, and local sessions still start.
