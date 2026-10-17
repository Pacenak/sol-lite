# Infrastructure automation: architecture and operator guide

## Delivery status

The infrastructure automation skill, command catalog and JSON Schemas are design assets. A credential-isolated SSH broker, fixed remote dispatcher, independent human approval service, configuration adapters and tool registration are **not implemented by these assets**. No remote infrastructure has been changed or certified by the documentation test round.

The existing `remote_execute` tool is a separate capability. It accepts free-form commands and approval IDs, permits timeouts up to 900 seconds, resolves command secrets, and returns redacted stdout/stderr. Its SSH transport uses the local OpenSSH client without explicitly setting the full new contract's host-verification, forwarding and noninteractive options. Existing permission and command guards remain relevant, but do not establish compliance with the new contract. Do not expose that tool as a fallback for this agent.

## Asset map

- [Skill entrypoint](../../skills/infrastructure-automation/SKILL.md): scope, deadlines, sanitization, workflow, GNU/BSD differences and containment.
- [Broker architecture](../../skills/infrastructure-automation/references/architecture.md): trust boundaries, dispatch, approval binding, tool semantics and deployment criteria.
- [Tool schemas](../../skills/infrastructure-automation/references/tool-schemas.json): closed model-input definitions and sanitized result envelope.
- [OS command catalog](../../skills/infrastructure-automation/references/command-catalog.md): requested OS/category/purpose/check tables, including configuration examples.
- [Test procedure and release gates](../testing/infrastructure-automation.md): repeatable local checks and required future runtime tests.

## Credential and execution flow

1. The authenticated caller selects an authorized opaque inventory machine ID such as `lab_linux_01`. IDs are identifiers, never bearer tokens.
2. The tool gateway validates the selected JSON Schema and rejects unknown fields. Caller identity, session scope and approval state come from the authenticated control plane, not model arguments.
3. Broker-only inventory resolves the ID to a destination, account, pinned host identity, supported OS/adapter, permitted resources and a credential-provider reference. Inventory is not returned wholesale to the model.
4. A local agent/keyring signs SSH challenges or a broker workload identity acquires a short-lived certificate. Keys, passwords, decryption tokens, sockets, provider responses and credential-bearing diagnostics stay outside model-readable storage and processes.
5. The broker connects to the pinned host and invokes one constant provisioned dispatcher command or subsystem. It sends bounded structured data separately. No model text is interpolated into the remote shell command. Dispatcher validates again and calls fixed absolute executables without a shell.
6. Purpose-built output parsers return bounded selected fields and typed statuses. Suppress raw output and arbitrary configuration files; unknown content fails closed. Redaction alone cannot guarantee the zero-credential requirement.

Provision the required SSH options listed in the architecture, administrator-owned dispatcher, approved startup path and remote watchdog before execution. Never use automatic host enrollment, agent forwarding, arbitrary `sudo`, interactive credential prompts or an agent-authored SSH configuration.

## Tool contracts

Each named definition under `$defs` is a separate input schema. The containing JSON file is a schema library, not a universal request validator: validating against the root alone does not select a tool contract. Resolve `#/$defs/<tool-name>` explicitly. `tool_result` is the shared response definition. No tools are registered by reading the file.

- `check_system_status`: machine ID, a bounded unique list of unprivileged check names, optional deadline up to 30 seconds. Example: `{"machine_id":"lab_linux_01","checks":["identity","interfaces","routes"],"timeout_seconds":20}`.
- `execute_remote_command`: machine ID, an enumerated read operation and resource ID where required. Despite its name, this tool accepts no shell command or argv. Example: `{"machine_id":"lab_linux_01","operation":"service_state","resource_id":"service_resolved"}`.
- `prepare_configuration_plan`: machine ID, managed resource ID and a typed desired change. Example: `{"machine_id":"lab_linux_01","resource_id":"service_ethernet","change":{"kind":"dns","servers":["192.0.2.53"]}}`. Documentation addresses are examples, not deployment recommendations. Planning performs no remote writes. Required privileged reads must already be authorized.
- `apply_configuration_plan`: machine ID and immutable plan ID only. Example: `{"machine_id":"lab_linux_01","plan_id":"plan_dns_001"}`. No tool argument grants human authorization.

`managed_configuration` references an administrator-reviewed structured desired-state object. It does not upload an arbitrary file, script or secret-bearing payload. Services, packages, paths and network service names resolve from scoped resource IDs; the model cannot choose executable paths. Unsupported OS/operation/resource combinations are rejected. Resource-specific requirements, IP address semantics, caller scope and policy require runtime checks in addition to schema validation. Enable JSON Schema format validation for IPv4 fields; it is not enabled by default by every library.

The response includes an operation ID, machine ID, typed status, sanitized summary and truncation indicator. `evidence_id`, when present, resolves to sanitized structured evidence. Plan preparation uses the operation ID as its non-authorizing plan ID; the authenticated approval UI fetches exact plan details directly from the broker. Do not rely on a prose summary to authorize executable changes.

## Human approval and change procedure

Read-only means an explicitly cataloged unprivileged observation. Administrative reads, candidate files, backups, package metadata refresh, configuration validation that writes files, network changes, rollback and reboot all require approval. Normal OS audit logging caused by a read does not make it a configuration change.

The dual gate means deterministic policy authorization **and** explicit human approval. It does not by itself mean two human approvers; configure separate reviewer identities if required by organizational policy. Approval must occur through an authenticated UI, not a model-accessible approval tool.

1. Establish host identity, OS release, network manager and resource ownership. Record live and persistent sanitized state and broker-held hashes. If tools or manager ownership are ambiguous, stop.
2. Compare desired and observed values. Return `NO_OP` when equal; do not rewrite configuration or restart services merely to run a procedure.
3. Prepare an immutable plan containing exact adapter/commands, target fingerprint, current-state hashes, desired state, privilege, candidate/staging effects, maintenance window, deadlines, postchecks, recovery access and rollback triggers. Do not include raw secrets or secret-bearing diffs.
4. Show the full plan to the authorized human. Store one-use approval bound to caller, session, target identity, plan hash, policy/adapter versions and expiry. Plan IDs grant no authority.
5. Lock the target, independently recheck state and policy, atomically consume approval and journal start. Drift requires a new plan and approval. Concurrent or replayed calls return recorded state without rerunning writes.
6. Stage, validate and activate only the approved bounded operation. Preserve permissions, owner and platform metadata; prevent symlink and path races. Do not append duplicate settings. Packages, firewall rules and manager activation require distinct reviewed adapters.
7. Verify persistent settings, effective addresses/routes/DNS, service health and controller reachability. Success requires postconditions, not only exit code zero. A reboot-based persistence check requires an approved reboot.
8. If verification fails, freeze further writes. Execute only an exact preapproved rollback whose trigger matches, or obtain a fresh recovery approval. Independently verify rollback. A connection loss is `OUTCOME_UNKNOWN`, never assumed success or failure.

For changes affecting the management path, verified out-of-band access and a bounded recovery mechanism are prerequisites. Netplan trial mode changes state and has rollback caveats; do not assume a disconnect means rollback succeeded. A noninteractive broker needs a specifically tested confirmation strategy.

## Platform handling

Ubuntu and Debian do not imply one network manager. Detect Netplan, systemd-networkd, NetworkManager or ifupdown and refuse conflicting ownership. Use the installed release's documentation. macOS network services and interfaces are different identifiers; names containing spaces must remain one argv element.

Use GNU `stat -c` on a compatible Linux adapter and BSD `stat -f` on macOS. Use `sha256sum` versus `shasum -a 256` through fixed adapters. Do not assume GNU `sed -i`, `readlink -f`, `grep -P`, `date -d`, `find -printf` or `timeout` on macOS. Prefer structured rendering over in-place text edits. Broker and remote watchdog enforce deadlines regardless of utility availability. POSIX shell templates must check exit statuses explicitly and cannot assume `pipefail` support.

## Fault handling and operator recovery

- `UNREACHABLE`: inspect approved inventory and network facts. At most two additional read attempts after 1 and 3 seconds. No automatic alternate targets or infrastructure repairs.
- `HOST_IDENTITY_BLOCKED`: stop; an administrator verifies the fingerprint out of band and updates trusted inventory. Do not delete known-host entries or weaken SSH verification.
- `AUTH_BLOCKED`: operator repairs keyring/certificate availability outside the agent context. Never paste credentials into chat or tool arguments.
- `APPROVAL_REQUIRED` / `PRECONDITION_FAILED`: retrieve the current plan state, re-read facts and obtain fresh approval when needed. Never reuse expired or changed approvals.
- `UNSUPPORTED` / `READ_FAILED`: report the missing capability or unsafe output. Use only an already registered read equivalent; do not install a utility or expand output access.
- `OUTCOME_UNKNOWN`: block new writes and reconcile the durable journal and remote completion using fresh safe reads. Do not replay the mutation. Local SSH termination alone does not prove remote cancellation.
- `VERIFICATION_FAILED` / `ROLLBACK_FAILED`: preserve the write freeze, sanitized evidence and operation IDs; involve the operator for approved recovery.
- `CONTAINED`: stop dispatch, close the session, revoke pending approvals and retain sanitized audit metadata. Unexpected shell prompts, privilege drift and output instructions do not authorize host isolation, reboot or process killing outside the approved boundary.

Record actor/session IDs, machine ID, plan and operation IDs, policy/adapter versions, approval decision, before/after hashes, sanitized verification and recovery state. Exclude credentials, raw command/config bodies, environment and raw stdout/stderr from logs and model context.

## Enablement checklist

Before exposing execution tools, implement and review inventory isolation, credential-provider boundary, authenticated approval UI, fixed dispatcher, per-OS catalog adapters, semantic validation, output extraction, one-use approval store, target locks, durable operation journal and remote watchdog. Remove alternative generic execution tools from this agent's allowlist. Run the runtime adversarial suite described in the testing guide on disposable Linux and macOS hosts with verified recovery access.

Until those checks pass, use this skill for architecture review and plan preparation only. Existing remote tests are regression evidence for existing behavior, not production certification of the new agent.
