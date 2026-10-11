# SOL-Lite standalone guide and Command link

## Decision

SOL-Lite stays independently usable. The operator guide leads with standalone install, daily use, and the optional SearXNG, Google, and Jira integrations. SOL-Command pairing is a later, optional chapter.

The link that gets proven is the one already implemented:

- `sol-lite connect` registers `client_type: sol-lite`, waits for Command approval, claims once, and stores the instance id and API key in the OS keyring.
- `sol-lite command-status` calls `GET /api/lite/v1/status`.
- The PA can read assigned-sector memories, search assigned-sector RAG metadata, and submit a Jarvis proposal.
- `sol-lite sync-skills` downloads assigned-sector pack bodies into pending review and does not activate them.
- `sol-lite disconnect` deletes the local keyring entry. A Command administrator revokes the instance separately.

These stay as they are: no background sync, no shared-data writes, no automatic skill install, and no Lite-side Jarvis approval.

## Identity rules

Command accepts a Lite claim only when the approved instance is `sol-lite`, and it rejects a claim whose `client_type` does not match that approved instance. `/api/lite/v1` rejects any instance that is not paired as `sol-lite`, including an Outpost key. Sector checks still run on every data request.

## Proof

SOL-Command contract tests cover register, approve, claim, mismatched claim, status, hidden API key, bad key, Outpost denial, unassigned sector denial, memory and RAG reads, pack sync limited to assigned sectors, Jarvis grant and pending ticket, and denial after the instance is removed.

SOL-Lite tests cover keyring pairing, disconnect, unpaired tool failure, and the doctor wording that separates the local bridge listener from Command pairing.

## Guide

The operator document is `docs/integrations/sol-lite.md`. `docs/integrations/sol-command.md` points at it.
