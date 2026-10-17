# Zero-trust broker contract

## Trust boundaries

LLM -> authenticated tool gateway -> policy engine + independent human approval service -> SSH broker -> fixed remote dispatcher -> approved OS adapter.

The model supplies an opaque `machine_id` and a catalog operation or sealed plan ID. A broker-only inventory maps that ID to destination, port, account, pinned host key, allowed operations, environment and credential-provider reference. Resolve machine scope against the authenticated caller before looking up access material. Never accept a host, username, key path, socket path, SSH options, authentication token or approval bearer token from model payloads.

A dedicated local SSH agent/keyring signs authentication challenges, or a broker workload identity obtains a short-lived SSH certificate from a secret manager. Keep private keys non-exportable where possible; certificate and signing handles remain in the broker boundary. Disable shell tracing and credential dumps; the LLM process cannot read broker files, environment, sockets or secret-manager APIs. Do not resolve secret placeholders in model-authored commands. Broker logs contain IDs, hashes and decisions, not raw command/configuration bodies. Secret-manager access and host enrollment happen outside the agent context.

Provision explicit SSH configuration: `BatchMode=yes`, `StrictHostKeyChecking=yes`, broker-managed known-hosts, `ForwardAgent=no`, `ForwardX11=no`, `ClearAllForwardings=yes`, `RequestTTY=no`, `PermitLocalCommand=no`, finite `ConnectTimeout`, `ServerAliveInterval` and `ServerAliveCountMax`. Disable password and keyboard-interactive authentication. Use only inventory-pinned identities; constrain destination and signing use. Disable user SSH config, multiplexing across identities, proxy commands and unapproved jump hosts. Certificate authentication still requires host verification. Server-side forced dispatcher, disabled PTY/forwarding, separate read account and narrow noninteractive privilege rules provide defense in depth. No general `sudo` or password input; privileged adapter access is allowed only after approval, including privileged reads.

## Defensive execution whitelist

JSON Schema validation is necessary, not sufficient. Reject unknown properties, oversize inputs, noncanonical IDs and unsupported versions. Public tools accept no arbitrary command or argv. Catalog operations map to exact administrator-owned executable paths, fixed subcommands, permitted flags, output extractors, OS versions and risk classifications. Resource IDs resolve to typed inventory values; validate addresses with an IP parser and interface/service membership against discovery. Never trust a model-provided `read_only` label.

OpenSSH remote command strings are interpreted by a remote shell. Do not assume passing a local argv array makes remote interpolation safe. Invoke one constant, provisioned dispatcher command; carry bounded structured JSON over stdin or an authenticated subsystem. Dispatcher calls executables without a shell. No payload interpolation into that constant command. Refuse shell operators, newlines, control characters, substitutions, redirection, environment assignment, globs and interpreter execution in any proposed shell text; escaping or a character regex is not the primary boundary. A novel command requires an administrator-reviewed catalog update, not a one-off whitelist bypass.

Read adapters return only explicitly selected safe fields; arbitrary `cat`, `env`, `ps` arguments, Wi-Fi profiles, connection secrets, private keys and unrestricted logs are excluded. Metadata and config summaries come from purpose-built parsers. Redaction is defense in depth after extraction. Errors use stable codes with bounded safe diagnostics; never forward raw stderr.

## Dual authorization and transaction semantics

## Tool binding rules

Register each input definition from `tool-schemas.json` as the named tool's JSON input schema. `tool_result` defines the common response envelope; `evidence_id` resolves only to broker-sanitized structured evidence. Plan preparation returns a `PLAN_READY` envelope whose `operation_id` is the non-authorizing plan ID; the human UI retrieves its immutable details directly from the broker. No approval-issuing tool is exposed to the model.

`check_system_status` batches bounded read adapters. `execute_remote_command` retains the familiar name but accepts only enumerated operations. Require `resource_id` for service, package, metadata and network-service checks; reject it for operations without resource parameters. Resolve IDs within caller scope and the selected machine. Unsupported operation/OS pairs fail closed. `prepare_configuration_plan` is controller-only planning and performs no remote staging writes; missing current facts must be collected with allowed read tools first. Any new privileged read needs approval before collecting it. `desired_state_id` references an administrator-reviewed structured configuration object, never a script or secret-bearing body. Parse all address literals semantically, reject unspecified/broadcast/multicast values when inappropriate, validate subnet/gateway consistency and enforce site address policy. JSON Schema `format` checks must be enabled explicitly or implemented in broker validation.

`apply_configuration_plan` performs the independently authorized execution; it accepts no approval credential or editable desired state. Omitted deadlines cannot disable default limits, and supplied limits can only shorten policy maxima. Schema validation alone does not implement these binding rules.

## Approval records

Gate A: deterministic policy checks target scope, operation, parameters, OS, privilege, impact, timing and recovery prerequisites. Gate B: a human approves the displayed exact immutable plan through an authenticated UI. Both must pass; policy may deny a human-approved request. Distinct human reviewers can additionally be required by organizational policy.

The broker canonicalizes and hashes the full executable plan including preconditions, desired state, staging/validation effects, postchecks, rollback, operation version and timeout. Approval service stores a short-lived one-use signed record bound to that hash, target host fingerprint, caller and session; tool payloads contain only non-authorizing plan IDs. The executor fetches the record over a separate authenticated channel. An ID alone grants nothing.

Serialize per target and atomically check drift, consume approval and journal operation start before dispatch. Repeated calls return the recorded result or `OUTCOME_UNKNOWN`, never apply again. Persist bounded execution and rollback state server-side; disconnects do not silently release writes. Verify remote completion and postconditions before unfreezing. Rollback is itself a mutation: include exact bounds and trigger in original approval or require new approval. No blanket emergency bypass.

Limits: connect 10s; read 30s; write 120s; total workflow 600s; 64 KiB safe output per operation; two read retries maximum. Broker and remote watchdog enforce limits. Expensive reads need separately reviewed resource limits. No automatic write retry. A timeout may leave a remote write running: freeze, reconcile, then recover.

## Integration status and acceptance criteria

These assets define a new contract; they do not register tools or alter existing execution permissions. The repository's existing `remote_execute` accepts free-form command text and has different limits. Do not expose it as a substitute in this agent's tool allowlist. Implement and review the broker, dispatcher, inventory, approval UI and output adapters before enabling this skill for execution.

Before deployment test: injection through every argument; unknown operation/flag/path; credential canaries in stdout/stderr/config; host-key mismatch; locked keyring; cross-tenant machine IDs; approval replay and expiry; changed plan/host/preconditions; two concurrent writes; SSH disconnect during apply; watchdog failure; rollback failure; unauthorized privileged reads; GNU/BSD capability mismatch. All must fail closed with sanitized results and no unapproved side effects. Skill validation cannot prove these runtime properties.

## Primary references

- [OpenSSH client options and host verification](https://man.openbsd.org/ssh_config)
- [Debian iproute2 syntax](https://manpages.debian.org/bookworm/iproute2/ip.8.en.html)
- [Apple networksetup documentation](https://support.apple.com/en-ae/guide/remote-desktop/apdd0c5a2d5/mac)
- [Ubuntu netplan try and rollback caveats](https://manpages.ubuntu.com/manpages/noble/man8/netplan-try.8.html)
- [GNU timeout behavior](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html)

Detect the installed release and consult its documentation before registering an adapter.
