# Link SOL-Lite to SOL-Command (beginner chapter)

If no logs or pending request appear, start with [terminal-to-Command real-world linking](../integrations/command-real-world-linking.md). SOL-Lite has no `/setup` website; run its `connect` subcommand in PowerShell/Terminal, while the administrator uses Command's Pair page. [Static code findings](../debugging/command-pairing-static-analysis.md) explain current silent progress, generic errors and one-time-claim recovery limitations.

This is the copy/paste runbook for **interns and engineers**. It covers the optional link from a local SOL-Lite install to studio **SOL-Command** (part of SOL-Full). Pairing is optional. SOL-Lite works fine alone.

**BookStack / bookshelf:** paste this file as a chapter. Each `##` heading below is a page you can split out later without rewriting.

Technical reference (API routes, tool table, limits): [SOL-Lite integration guide](../integrations/sol-lite.md) and [SOL-Command connection](../integrations/sol-command.md).

**Rules**

1. Do not paste invite codes, instance ids, or API keys into tickets, screenshots, or score sheets.
2. Use the studio Command host only when you are supposed to. Lab hosts stay on lab hosts.
3. Lite pairs as `sol-lite`. It is **not** an Outpost. Do not reuse an Outpost key.
4. An administrator must approve the pending instance on Command. Lite cannot approve itself.

Studio Command base URL (HTTPS, no port, no path):

```text
https://sol-command.corp.pacenlife.com
```

Use your real project path if it differs from the examples.

---

## Overview (who needs what)

| Role | You do this |
|---|---|
| Intern / engineer on a Lite machine | Run `connect`, wait for approval, run `command-status`. Optionally `sync-skills`. |
| Command admin / studio lead | Create the invite for the right sectors, approve the pending `sol-lite` instance, optionally grant Jarvis `lite-access`, delete the instance when done. |
| Anyone | Read [Lite vs Command vs Outpost](#lite-vs-command-vs-outpost) once so you do not mix clients. |

**Order that works**

1. Admin creates invite (sectors decided).
2. Operator runs `sol-lite connect` with that invite and waits.
3. Admin approves the pending instance as `sol-lite`.
4. Operator finishes claim, then runs `command-status`.
5. Optional: admin grants Jarvis; operator runs `sync-skills` and reviews pending skills.

---

## Lite vs Command vs Outpost

| Piece | What it is | Pairing for Lite? |
|---|---|---|
| **SOL-Lite** | Local multi-agent runtime on your Windows or macOS machine | This machine runs `sol-lite connect` |
| **SOL-Command** | Shared hub: instances, sectors, skill packs, Jarvis grants | Yes — optional HTTPS link |
| **Outpost** | Another SOL-Full client type (web hub / sector runtime family) | **No** — Outpost keys cannot call `/api/lite/v1` |

**Do not confuse**

- Pairing Command does **not** turn Lite into an Outpost.
- An Outpost instance key will fail Lite status and tools. Pair again as `sol-lite` with a Lite invite.
- Google, Jira, and SearXNG are separate. They do not create a Command instance.
- The `bridge` block in `config/sol-lite.yaml` is a local listener switch. It is **not** the Command pairing switch. Leave it off unless you have a reason to enable it.

---

## Admin half (invite, approve, Jarvis, revoke)

Do this in SOL-Command. Exact menu names may differ by Command version; the outcomes below are what must be true.

### A1. Create an invite

1. Choose the **sectors** this Lite machine is allowed to use.
2. Create a one-time **invite** for a **SOL-Lite** client (not Outpost).
3. Give the invite code to the operator out of band (chat, Bitwarden, in person). Do not commit it to git.

### A2. Approve the pending instance

1. After the operator runs `connect`, a **pending** instance appears on Command.
2. Confirm `client_type` is **`sol-lite`**.
3. Approve it with the intended sector assignment.
4. Tell the operator approval is done so their `connect` can finish claiming.

Lite cannot self-approve.

### A3. Optional — grant Jarvis propose (`lite-access`)

Jarvis submission from Lite stays **off** until you grant it. When the product UI is not available, the documented grant is:

```http
PATCH /api/hub/instances/{instance_id}/lite-access
Content-Type: application/json

{"jarvis_propose": true, "jarvis_domains": ["skills", "code_fix"]}
```

The Lite client accepts `meal_plans`, `fitness_plans`, `skills`, `memories`, `home_pa`, and `code_fix`. Command also requires its Jarvis persona policy to allow that domain. A successful Lite proposal stays **pending** for Command review. Lite cannot approve or apply it.

Skip this step for most intern pairing drills.

### A4. Revoke when the machine should leave

1. Ask the operator to run `sol-lite disconnect` (removes the local keyring credential only).
2. On Command, delete the instance (documented API: `DELETE /api/hub/instances/{instance_id}`).
3. After deletion, their `command-status` and Command tools fail. Local Lite sessions still work.

---

## Operator half (connect, status, sync, disconnect)

Work from the SOL-Lite project directory. Windows examples use PowerShell.

### O1. Confirm standalone first (optional but good for interns)

```powershell
cd E:\git\plg-sol\PLG_Ai_Lite
.\.venv\Scripts\sol-lite.exe doctor
```

macOS / Linux:

```bash
cd ~/git/PLG_Ai_Lite
.venv/bin/sol-lite doctor
```

Expect `SOL-Command: not paired (standalone)` if you have never paired. `doctor` does **not** call Command over the network.

### O2. Connect and wait for admin approval

Windows:

```powershell
.\.venv\Scripts\sol-lite.exe connect --command-url https://sol-command.corp.pacenlife.com --invite-code YOUR_INVITE
```

macOS / Linux:

```bash
.venv/bin/sol-lite connect --command-url https://sol-command.corp.pacenlife.com --invite-code YOUR_INVITE
```

- Replace `YOUR_INVITE` with the real code. Do not put the code in docs or tickets.
- `--name` defaults to `SOL-Lite`.
- The command registers `client_type: sol-lite`, then **waits** until an administrator approves the pending instance.
- After approval it claims once, prints instance id and sectors, and stores the instance id + API key in the **OS keyring**. Not in `.env`, not in git.

HTTPS is required for non-loopback hosts. The URL must be a base URL (no user, password, query, or fragment).

### O3. Live check

```powershell
.\.venv\Scripts\sol-lite.exe command-status
```

```bash
.venv/bin/sol-lite command-status
```

Pass: you see instance id, assigned sectors, and `lite_access` info. You must **not** see the API key. Use this when you need to know Command is reachable. `doctor` only says whether a credential is saved.

### O4. Optional — download sector skill packs for review

```powershell
.\.venv\Scripts\sol-lite.exe sync-skills
```

```bash
.venv/bin/sol-lite sync-skills
```

Packs land under:

```text
data/state/skills/pending/sol-command/<sector-slug>/<skill-slug>/<content-hash>/SKILL.md
```

Nothing there is active until you inspect and import (`/skills discover` / `/skills import`). Sync does not install the whole SOL skill library.

### O5. Disconnect locally

```powershell
.\.venv\Scripts\sol-lite.exe disconnect
```

```bash
.venv/bin/sol-lite disconnect
```

This removes the local keyring entry only. Ask an administrator to delete the instance on Command if the machine should stay off the hub.

---

## After pairing (what works, what does not)

Only **`sol_pa`** gets Command tools (`sol_command_status`, shared memories, RAG search, Jarvis propose). Engineer, Docs, and Business do not.

| Expect | Do not expect |
|---|---|
| Read assigned-sector memories and RAG metadata when paired | Background sync; Lite copying Command data into local memory |
| Skill packs staged under `pending/sol-command/` | Auto-activate or overwrite installed skills |
| Jarvis propose only after `lite-access`, then **pending** ticket | Lite approving or applying Jarvis changes |
| Local agents, workspaces, and skills keep working if Command is down | An Outpost key working on Lite APIs |

Every remote call still goes through Lite’s network permission and approval policy. Unassigned sectors are denied even if someone types the id.

---

## Troubleshooting

| Symptom | Likely cause | What to try |
|---|---|---|
| `connect` waits forever | Admin has not approved, or wrong Command URL | Confirm URL; ask admin to approve pending **sol-lite** instance |
| Claim / status fails after “approval” | Instance approved as Outpost or wrong client type | Admin must approve as `sol-lite`; do not reuse an Outpost key |
| `doctor` says paired but tools fail | Credential saved; Command unreachable or instance deleted | Run `command-status`; ask admin if instance still exists |
| Jarvis propose denied | No `lite-access` grant | Admin grants domains; or skip Jarvis for this machine |
| `sync-skills` empty / unexpected | No assigned sectors or no applied packs | Check sectors on `command-status`; confirm packs on Command |
| HTTP rejected for studio host | Non-loopback must be HTTPS | Use `https://sol-command.corp.pacenlife.com` |

More detail: [SOL-Lite integration guide](../integrations/sol-lite.md).

---

## Lab sheet (interns)

Fill this in for a pairing drill. Do **not** write the invite code or API key here.

| Item | Your value |
|---|---|
| Date and timezone | |
| Your name | |
| OS | Windows / macOS |
| SOL-Lite folder | |
| `sol-lite version` | |
| Command URL used | |
| Admin who approved | |
| `command-status` sectors (names only) | |
| Jarvis grant used? | yes / no |
| `sync-skills` run? | yes / no |
| Disconnected after drill? | yes / no |

**Pass bar for a basic drill**

1. Admin created a Lite invite for known sectors.
2. Operator `connect` finished only after approval.
3. `command-status` shows instance id and sectors, with no API key.
4. Optional: `sync-skills` wrote pending files only.
5. Optional: `disconnect` + admin delete; later status fails; local Lite still starts.
