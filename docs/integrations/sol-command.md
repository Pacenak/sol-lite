# SOL-Command connection

SOL-Lite is usable on its own. The SOL-Command connection is optional and does not move Lite workspaces, local memory or credentials to Command.

## Pair

1. Create an invite in SOL-Command for the sectors this Lite instance should use.
2. On the Lite machine, run `sol-lite connect --command-url https://<command-host> --invite-code <invite>`.
3. An administrator approves the pending **SOL-Lite** instance in Command.
4. Check the result with `sol-lite command-status`.

Pairing follows Command's one-time invite, approval, token and claim-nonce flow. The resulting instance credential is saved in the OS keyring and is not written to `.env`, repository settings, logs or model context. HTTP is permitted only for loopback Command URLs; use HTTPS for LAN/VPN hosts.

Disconnect removes Lite's local keyring entry. It does not revoke the instance on Command; an administrator must also remove/revoke that paired instance there.

## Shared data

The `sol_command_status`, `sol_shared_memories` and `sol_shared_rag_search` tools call `/api/lite/v1`. Command checks the credential and current assigned-sector membership on every request. Memory reads exclude proposed/unapproved entries. Network calls pass Lite's network permission and approval policy. Command data remains remote and is not copied into Lite's local memory store.

## Skills

Run `sol-lite sync-skills` to fetch current assigned-sector pack bodies. Skills are materialized under `data/state/skills/pending/sol-command/` by sector, skill ID and content hash. This command does not activate them. Review each candidate, then use `/skills discover <path>` and `/skills import <skill>` to inspect and approve installation. Re-syncing new content creates a separate hash-versioned pending copy; local installed skills are not overwritten or deleted.

## Jarvis proposals

Jarvis proposal submission is off until a Command administrator explicitly grants an instance access. The administrative route is:

```http
PATCH /api/hub/instances/{instance_id}/lite-access
Content-Type: application/json

{"jarvis_propose": true, "jarvis_domains": ["skills", "code_fix"]}
```

The Command Jarvis policy must also allow its configured Jarvis persona to propose in that domain. Lite's `sol_jarvis_propose` tool requires network approval. Command records the Lite instance as the actor and returns a pending ticket; Lite cannot approve or apply it.

Supported proposal domains are `meal_plans`, `fitness_plans`, `skills`, `memories`, `home_pa` and `code_fix`. Enable only the domains appropriate for that instance.

## Offline and standalone behavior

If Command is unreachable, local Lite tools, agents, workspaces, models and skills remain usable. Remote tools return an explicit error; remote results are never silently substituted with local results. If Command revokes the instance or changes sector assignment, subsequent requests are denied by Command.

## Current limits

- Pairing is available through the CLI; there is no background synchronization loop.
- `sync-skills` downloads skill instructions from applied sector packs. It does not sync SOL's entire shared skill library or install anything automatically.
- Shared data support is read-only for memories and RAG.
- Jarvis support submits allowlisted proposals. It does not expose Jarvis monitoring internals, approvals, or auto-apply operations.
- SOL's network documentation describes a pre-production system. Validate the Command host and its security posture before LAN/VPN use.
