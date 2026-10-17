# Windows, network scope and protected machine facts

This extends the broker design contract. Windows adapters, protected fact storage and access enforcement are not implemented by reading this document or its schemas. Current generic PowerShell remoting is not a substitute for a constrained endpoint.

## Actual logged-in execution context

The broker authenticates a session and runs one fixed bounded identity collector on that target. Inventory platform is an expectation, not proof. Bind results to opaque `machine_id`, `execution_context_id`, broker-issued `session_id`, collector/adapter version, host-identity digest, observation time and expiry. Check target identity on every connection and require facts no older than five minutes before planning/applying; refresh after reconnect, reboot or execution-context change. Use a shorter policy TTL where needed. Never infer a remote OS from local `platform.system()`.

- Windows: select `Caption`, `Version`, `BuildNumber`, `OSArchitecture` from `Get-CimInstance -ClassName Win32_OperatingSystem` inside a trusted collector. Normalize OS family to `windows`; do not infer the OS from PowerShell availability. Collect PowerShell edition/version separately using the trusted `$PSVersionTable` values.
- Linux: kernel identity plus explicitly parsed `ID`, `VERSION_ID` fields from a bounded trusted `/etc/os-release` resource. Never source it. Distinguish Ubuntu, Debian and unsupported distributions.
- macOS: `uname -s` and `sw_vers -productVersion` from fixed executable paths. Report `macos`, not the controller's platform.
- WSL/container: report the Linux guest OS plus the execution boundary. A Microsoft kernel marker suggests WSL but is not sufficient to establish WSL version or host control. Use corroborating trusted broker provisioning; otherwise mark the boundary `unknown`. A Linux container says nothing about permission to configure its host network. PowerShell on Linux remains Linux; CMD/Git Bash on Windows do not make the kernel Linux.

OS strings alone are not authenticated attestation. A compromised host can lie; compare the collector's verified provenance and inventory expectation and return `IDENTITY_MISMATCH` on inconsistency. Unknown facts are explicit; do not guess. No passwords, login usernames, private keys, tokens, host serials, arbitrary paths, process arguments or credential-bearing configuration belong in fact snapshots.

## Protected per-machine file and agent access

Use [machine-facts.schema.json](machine-facts.schema.json) for the broker-private snapshot. Store it outside repository/workspace/memory/index/search roots as `<broker-private-state>/machines/<machine_id>/<execution_context_id>.json`. These are conceptual broker-owned paths, not model-provided paths. Atomic writes, validated schema, restrictive owner/ACL, integrity digest and durable audit are mandatory. Do not create a real machine file in this repository; only synthetic examples belong in tests.

OS access: a dedicated broker service identity owns the directory. On Linux/macOS require owner-only directories/files (0700/0600, verify effective ACLs as well); on Windows disable inherited broad access and allow only the broker service identity and required system/administrative recovery principals through an explicit NTFS DACL. Validate ACLs after replacement. If the platform/storage cannot enforce isolation, do not persist facts. Provisioning ACLs is administrative and human-approved.

OS permissions distinguish service identities, not agents sharing one process/account. Enforce agent access at an authenticated broker API and prevent generic file, terminal, search, backup and memory tools from reaching private state. If agents retain arbitrary execution under the broker's OS identity, the requested isolation is impossible; do not enable facts persistence under that deployment. Use a separate service identity/process boundary and protected IPC. Host administrators remain trusted recovery principals.

Authorization is default-deny and uses authenticated runtime principal + active task assignment + target/context scope + operation + field group + expiry. Never accept `agent_id`, `role`, `can_read`, `can_edit` or ACL policy in model input. Hiding a tool from the prompt is not authorization. Recheck on every request, including cached facts; revoke on reassignment/session end and prevent cross-agent memory leakage.

- A troubleshooting agent explicitly assigned the machine may receive `os` fields only.
- An assigned infrastructure agent may receive `os` and approved `capabilities` fields; network topology requires a separate scoped grant.
- A trusted collector may propose a refreshed snapshot only for its bound target/session. Publishing or editing a persisted file requires policy and an approved exact write, including the initial creation. A read-only OS check must not silently write a snapshot.
- Inventory administrators approve expected platform and access-policy changes separately. No ordinary agent can grant itself access, alter session identity, extend TTL or edit OS facts as prose. Corrections use a freshly verified collector and compare-and-swap revision; manual overrides are separately signed, clearly labeled and never replace observed evidence.

`get_machine_facts` accepts a machine ID and desired field groups. Context and session are resolved from the broker's authenticated connection; if more than one execution context matches, return `CONTEXT_REQUIRED` through the control plane and do not guess. An absent grant returns `ACCESS_DENIED` without revealing whether a machine file exists. Stale authorized data returns `FACTS_STALE`; refresh only through allowed read collection, without automatic persistence. Response evidence is field-projected and access-checked; never return the entire private file by default.

## Windows read and write paradigms

Use Windows PowerShell 5.1 or supported PowerShell 7 as detected; module availability and remoting serialization vary. Specify module-qualified cmdlets in registered adapters where practical. Build typed parameter dictionaries in trusted code and invoke fixed cmdlets; never concatenate a remote script from values. Use a provisioned JEA endpoint over authenticated Kerberos or validated HTTPS/SSH transport as appropriate. No wildcard TrustedHosts, certificate-check skipping, CredSSP/credential delegation, SMB fallback or domain-policy bypass. Authentication handles stay in the broker.

For Windows read catalog rows see [command catalog](command-catalog.md#windows-command-catalog). Output is selected structured properties, bounded and sanitized before reaching the model. Elevation requirements vary by OS/module and must be checked by policy; an administrative read always needs approval. Profiles disabled and `-NonInteractive` do not by themselves constrain command access.

For approved changes: DNS uses `Set-DnsClientServerAddress`; address/DHCP configuration uses the appropriate `New-NetIPAddress` / `Set-NetIPInterface` adapter; routes use precise `New-NetRoute` / `Set-NetRoute` operations; firewall uses owned named rules via `New-NetFirewallRule` / `Set-NetFirewallRule`. A static-address adapter must explicitly handle existing addresses, DHCP transitions, duplicate-address detection and persistent/active policy stores. Never blindly add the same address or rule repeatedly. Compare before/after normalized desired values and effective policy. Group Policy/MDM may own settings; report managed ownership instead of overriding it. Any restart, cache flush, renew/release or connection reset is a mutation.

## Network use when needed

Passive network state includes interfaces, IPv4/IPv6 addresses, routes, DNS servers, neighbors and listener summaries within the assigned machine. Names, addresses and topology are sensitive operational facts and are released only to assigned agents. Query only relevant fields; no packet payloads, Wi-Fi keys, unrestricted VPN profiles or proxy credentials.

Active probes use `probe_network_endpoint(machine_id, endpoint_id, probe, timeout_seconds)`: destination IDs resolve to broker-owned allowed host/IP/port records with explicit IPv4/IPv6 policy, maximum attempts and intended source context. Require a separate egress/probe grant even for read-only diagnostics. DNS lookups must use approved resolver/query records; revalidate resolved addresses at connection time to prevent rebinding. Deny metadata services, loopback, link-local and private ranges unless explicitly allowed for that target and purpose. Do not treat all internal subnets as authorized. Validate every redirect or disable redirects entirely.

Allowed adapters may provide bounded ICMP, DNS and TCP-connect probes. Windows can use constrained `Test-NetConnection` / `Resolve-DnsName` through exact registered parameter sets; Linux/macOS equivalents must have fixed tool/version support. No arbitrary HTTP requests, port ranges, UDP broadcast, discovery sweeps or continuous polling. Captures, scans, device admin and VPN/firewall/routing changes require separate reviewed capabilities and human approval where mutating or administrative. Unsupported network devices fail closed.

## Additional faults and tests

`IDENTITY_MISMATCH`: stop writes, invalidate facts/approvals, investigate verified host identity. `FACTS_STALE`: collect fresh authorized observations; publishing them is separately approved. `ACCESS_DENIED`: reveal no existence or topology. `CONTEXT_REQUIRED`: bind the intended session through the authenticated control plane. `NETWORK_SCOPE_DENIED`: no probe or alternate destination. WinRM certificate/SPN/Kerberos failures are `AUTH_BLOCKED` or host identity failures, never reasons to weaken transport security. Unsupported JEA/cmdlet/module versions return `UNSUPPORTED`.

Test Windows host versus WSL guest, PowerShell on Linux, container namespaces, stale snapshots, forged session identity, cross-agent file/API reads, direct terminal bypass, field projection, grant revocation, compare-and-swap conflicts, snapshot integrity/ACL replacement, denied network ranges, DNS rebinding, IPv6 scope and Windows managed-policy ownership. These require runtime integration tests in addition to schema tests.

## Primary references

- [Microsoft Get-NetIPConfiguration](https://learn.microsoft.com/en-us/powershell/module/nettcpip/get-netipconfiguration)
- [Microsoft JEA security considerations](https://learn.microsoft.com/en-us/powershell/scripting/security/remoting/jea/security-considerations)
- [Microsoft WSL versions](https://learn.microsoft.com/en-us/windows/wsl/wsl2-about)
