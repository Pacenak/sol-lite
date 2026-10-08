# SOL-Lite and SOL-Command integration

## Purpose

SOL-Lite remains an independently installable, local-first application. Pairing it with SOL-Command adds an optional network connection for Command-approved sector context, skills, policy and Jarvis services. When Command is unavailable or Lite is unpaired, local sessions, models, workspaces, memory, tools and skills continue to work.

## Current implementation boundary

SOL-Lite has a `bridge` settings section, but `Runtime.health_check()` reports that the bridge is not implemented. Its MCP client/server and credential abstractions are not yet composed into a SOL-Command connection. The skill manager supports inspection, provenance, quarantine and approval-oriented installation, but the app does not sync SOL packs.

SOL-Command already has device pairing, instance credentials, sector assignment, and paired-instance pack/fleet sync routes. Its shared-data routes currently mix user-authenticated and instance-authenticated access: some operations allow an instance credential, while memories and RAG reads require an authenticated user. Its Jarvis Evolve routes require user privileges. Do not treat an instance key as a user identity or grant it those routes implicitly.

## Working-tree implementation in this change

- SOL-Lite has `connect`, `command-status`, `disconnect` and `sync-skills` CLI commands. Pairing uses a distinct `sol-lite` client type, Command approval and keyring storage.
- Command has `/api/lite/v1/status`, assigned-sector-scoped memory/RAG reads, and an explicitly admin-granted, proposal-only Jarvis route.
- SOL-Lite exposes status, memory and RAG agent tools through the existing network permission boundary.
- `sync-skills` downloads applied assigned-sector pack skills into a content-hash-versioned pending-review directory. It never activates them automatically.

The repository work is an initial vertical slice, not every item in the target design. There is no background sync, local UI for integration administration, shared-data write path, complete skills-library sync, automatic tombstone/removal handling, or broad Jarvis task delegation. Run the cross-repository acceptance scenarios before treating the bridge as release-ready.

## Target architecture

```text
SOL-Lite (standalone runtime)
  local sessions / workspaces / models / skills / audit
  optional SolCommandConnector
      | HTTPS, paired instance identity, explicit endpoint allow-list
      v
SOL-Command
  pairing + instance registry + assigned sectors + policy + audit
  shared data API / pack and skill sync / Jarvis request broker
```

Command is the authority for network identity, assigned sectors and network policy. Lite owns its local workspaces, credentials, approvals, sessions and local data. Data moves only through documented APIs, never direct database access, a shared filesystem mount, or imports from the other repository.

## Required implementation work

### 1. Pairing and connection lifecycle

- Add a Lite client for the Command pairing register, status and claim flow. Pairing must remain human-approved by a Command administrator and use the existing one-time invite, token and claim nonce rules.
- Add an explicit Lite product/client identifier and a compatibility rule on Command. Do not pretend a Lite version is an Outpost product version; keep Lite and Command release versions separately visible.
- Store the resulting instance ID and API key in the OS credential store. Store only non-secret connection metadata in user settings. Support disconnect, credential revocation, reconnect and health status.
- Use HTTPS for non-loopback Command URLs, bounded timeouts, response-size limits, and redacted logs. Never put API keys in model context, tool results or URLs.
- Keep connection optional. A network failure must not disable local operation.

### 2. Narrow shared-data API

- Add instance-authenticated, assigned-sector-scoped read endpoints for the data Lite actually needs, initially approved memories and RAG search.
- On every request, verify the instance credentials and confirm the requested sector is currently assigned to that instance. Do not rely only on a client-supplied sector list.
- Keep writes disabled initially. Later add narrowly scoped proposal/write endpoints with actor attribution, audit, quotas and human approval where appropriate.
- Display source and sector on returned context so agents can distinguish local data from Command data.

### 3. Skills and pack synchronization

- Reuse the paired-instance `/api/hub/sync/packs` route as the transport only after documenting and validating the pack payload Lite consumes.
- Sync only assigned-sector packs. Validate every skill's frontmatter, file paths, symlinks, file sizes and content hash before it reaches the active skill set.
- Maintain a separate managed Command-synced skill store. Preserve built-in and user skills; record source, sector, pack version/hash, status and sync time.
- Changed skills must be inspected and either explicitly auto-approved by a Command policy or held pending local review. Command provenance alone does not grant tool permissions.
- Define update and removal/tombstone semantics so revoked skills do not stay active indefinitely. Retain a rollback copy and local override behavior.
- Curate compatibility rather than copying every SOL skill. Begin with general research, documentation and engineering workflows. Add marketing, studio and game-development skills only when their required context and tools are available.

### 4. Jarvis request broker

- Add a dedicated Command API for paired Lite instances. Do not expose the user-session `/api/evolve/*` routes directly to instance keys.
- Command administrators must opt in each instance and assign allowed operations/domains. Every request must be constrained to the instance's assigned sectors, logged with the instance actor, and rate-limited.
- Start with status/read and proposal submission. Proposals remain pending for Command-side review; Lite cannot approve or apply its own proposals.
- Return a stable request ID, state and bounded result/evidence. Do not forward unrelated user data or secrets to Jarvis.

### 5. Lite user experience and local policy

- Replace the placeholder bridge warning with paired/unpaired, reachability, assigned-sector, last-sync and permission status.
- Provide explicit commands/UI for connect, status, sync, disconnect and local-vs-Command skill inspection.
- Add a local policy layer for each remote operation. Command policy may narrow Lite permissions, but remote capabilities still pass Lite's permission, approval and audit checks.
- Label remote tools with network risk and origin. No remote or mutating capability is exposed through MCP unless separately allow-listed and authorized.

## Delivery sequence

1. Audit endpoint auth and payload contracts; define a Lite client version/protocol contract.
2. Implement pairing, secure credential storage, status and offline behavior.
3. Add sector-scoped read-only shared memory/RAG endpoints and Lite tools.
4. Add validated, provenance-preserving skills sync with update/removal behavior.
5. Add the opt-in Jarvis request broker and pending-proposal flow.
6. Consider writes only after the read-only path, audit and approval behavior are established.
7. Document and execute acceptance scenarios: standalone mode, pairing approval/rejection, revocation, offline recovery, assigned-sector isolation, malformed/changed skill packs, Jarvis proposal review, and independent version upgrades.

## Acceptance criteria

- A fresh Lite install works without Command URL or credentials.
- Pairing cannot complete without Command administrator approval and yields no reusable secret in UI logs or model context.
- A paired instance can access only its assigned sectors, even if a caller substitutes a different sector ID.
- Command data is read-only in the initial release and clearly attributed.
- Invalid or changed skills never silently become active; revocations and removals take effect on sync.
- Jarvis calls are opt-in, scoped, audited and proposal-only until Command approval.
- Command downtime leaves Lite local features available and reports stale remote context accurately.
- SOL-Lite remains separately installable and does not require PLG_Ai_Interface Python modules or its database.

## Source repositories

- SOL-Lite runtime and settings: `src/sol_lite/core/runtime.py`, `src/sol_lite/bootstrap.py`, `config/sol-lite.yaml`.
- SOL-Lite skill lifecycle: `src/sol_lite/skills/manager.py`, `docs/architecture/skills.md`.
- SOL Command pairing/sync: `routes/hub_routes.py`, `hub/registry.py`, `src/outpost_client.py`.
- Shared data: `routes/shared_data_routes.py`.
- Jarvis Evolve: `routes/evolve_routes.py`, `hub/evolve_system.py`.
- SOL network documentation labels the network as pre-production; verify live wiring against `docs/system-audit/` before deployment.
