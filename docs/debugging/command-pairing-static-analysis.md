# SOL-Lite / Command linking: static code analysis

Inspected 17 October 2026. Scope: Lite client, CLI dispatch, bootstrap/keyring handling, Command pairing routes/registry/auth middleware, Pair UI source and existing tests. No app, service, test or pairing request was run. This is a documentation deliverable; no implementation fixes were made.

Reported symptom: the operator sees no meaningful terminal logs and no pending client in Command. Source establishes several visibility/recovery defects, but cannot identify the deployed host's root cause without its HTTP result and stage evidence. Use the [real-world linking runbook](../integrations/command-real-world-linking.md) to collect that evidence without exposing keys.

## Terminal versus browser is not a protocol incompatibility

Lite runs `connect` from the operating-system terminal. Its Python HTTP client calls Command directly. Command's administrator alone opens `/command/pair/`. There is no Lite `/setup` webpage and no implemented chat slash command `/connect`.

The checked protocol aligns:

1. Lite posts token, claim nonce, invite, name/host hint and `client_type: sol-lite` to `/api/hub/pair/register`.
2. Command accepts `sol-lite`, stores it on the pending row and returns `pending_id`/`state`.
3. Lite polls `/api/hub/pair/status` using the generated token.
4. Admin approval preserves `client_type`, creates an unclaimed instance and consumes the invite/token.
5. Lite posts the same nonce/type to `/api/hub/pair/claim`; the server returns `credentials.instance_id`, `api_key` and sectors.
6. Lite saves them to its current user's keyring. Later requests send `X-Sol-Instance-Id` and `X-Sol-Instance-Key` to `/api/lite/v1/...`.

The server exempts the machine bootstrap routes and `/api/lite/` from ordinary user-cookie auth when running as a Command hub. Each Lite data route still verifies its instance credentials and type. Admin invite/approve endpoints remain administrator-protected.

Source: [Lite client](../../src/sol_lite/integrations/sol_command.py), [CLI](../../src/sol_lite/app.py), [Command routes](../../../PLG_Ai_Interface/routes/hub_routes.py), [registry](../../../PLG_Ai_Interface/hub/registry.py), [Lite bridge](../../../PLG_Ai_Interface/routes/lite_bridge_routes.py), [middleware](../../../PLG_Ai_Interface/app.py).

## Confirmed finding 1: silent progress and lost pending identity

**Priority: P2.** `SolCommandClient.pair()` ignores the successful registration response payload, including `pending_id`, and has no logging/progress callback. `app.py` prints only final failure or success. While registering/polling, the operator cannot tell which stage is active or identify the pending request to the administrator.

This directly explains why the terminal can appear silent. It does **not** establish whether the reported attempt reached Command. Python unbuffered mode cannot fix absent log statements.

**Proposed repair:** expose a safe progress callback and print stage changes, canonical host, elapsed approval wait and pending ID; no token, nonce, invite, credentials or full token-bearing URL. Surface registration success separately from approved/claimed/saved/verified. Keep repeated polls quiet except for a bounded heartbeat.

**Verification needed:** mocked pending-to-approved flow emits stages in order; rejected/error flows identify the correct stage; a real lab registration's pending ID correlates with Command UI. Existing [Lite pairing tests](../../tests/unit/test_sol_command.py) use mocked HTTP/keyring success and do not establish deployed end-to-end pairing.

## Confirmed finding 2: HTTP failures discard the reason and stage

**Priority: P2.** The single `HTTPStatusError` handler reports only `SOL-Command pairing returned HTTP N`. Registration, status and claim failures use that same wording. Command provides distinct details for expired/used/reserved invites, missing sectors and claim conflicts, but Lite does not retain a safe reason or the failed stage. Transport exceptions similarly collapse to class names.

An HTTP 400 from an expired invite and an HTTP 400 for a reservation conflict look identical to the user. It is therefore unsafe to infer one exact cause from the generic error.

**Proposed repair:** wrap each stage, preserve method/path category/status and classify allowlisted error codes/reasons, with sanitisation and length limits. Do not dump arbitrary upstream bodies or `request.url`: the status query contains the pairing token. Include a correlation identifier only if the backend supplies a safe one.

**Verification needed:** register 400, status 401, claim 409/410, redirects, TLS/network errors and HTML responses produce distinct useful safe diagnostics; secret-valued fixtures never appear in output.

## Confirmed finding 3: a successful one-time claim can be lost before local storage

**Priority: P2.** Command's `claim_instance_by_token()` sets `claimed=True`, clears the plaintext token/nonce and writes registry state before returning credentials. Lite only then calls `CredentialManager(KeyringBackend()).store()`. A keyring failure after the response leaves a consumed server claim without saved local credentials. A lost claim response creates a similar recovery risk.

Lite has no persistent pending-attempt state, resume command, acknowledgement protocol or safe claim recovery. Calling `connect` again generates a new token/nonce; it cannot recover the original one. The consumed/reserved invite may prevent reusing the same invite.

**Proposed repair:** preflight a safe keyring write/delete round-trip before registering, report storage failure as a distinct post-claim stage and provide an explicit administrator recovery procedure. A robust recoverable claim protocol requires coordinated server/client design; do not make credential claims generally replayable or write keys into plaintext files as a quick fix. Pending state, if persisted, must itself be protected.

**Current operator recovery:** repair the current user's keyring; have the administrator identify/retire only the orphaned instance and issue a fresh invite. Do not print claimed credentials to work around storage errors.

**Verification needed:** keyring write failure and a lost HTTP claim response preserve an honest state/error and a documented recovery outcome. No test should falsely mark the original pairing recoverable by calling the current `connect` again.

## Confirmed finding 4: rejection/expiry state does not match the client's loop

**Priority: P2.** Lite checks for `state == rejected` and `approved`; all other states continue sleeping. The checked Command reject route removes the pending row, and `pairing_status_for_token()` then returns `unknown`, not `rejected`. Expired pending requests can also become `unknown`. `claimed` is another server state the client's loop does not explicitly handle.

Therefore explicit rejection can appear as silent waiting until the generic administrator-approval timeout. A transient status failure instead aborts the whole attempt immediately; the client does not resume/retry it safely.

**Proposed repair:** define the full shared state machine, preserve server rejection/expiry outcomes where appropriate, handle invalid/unknown/claimed explicitly, and add bounded transient retry/resume behavior tied to the same protected attempt identity. Distinguish “never registered”, “expired”, “rejected” and “claim uncertain”.

**Verification needed:** rejected, expired, unknown and claimed sequences terminate or recover according to a shared contract; retry does not register a second unrelated pending client or leak keys.

## Confirmed finding 5: malformed base paths are accepted, redirects are refused

**Priority: P2.** `SolCommandConfig.__post_init__()` rejects credentials/query/fragment and non-HTTPS remote hosts, but does not reject non-root paths. Passing a browser page such as `https://host/command/pair/` passes validation; API suffix concatenation then targets the wrong URL. Both pairing and regular requests use `follow_redirects=False`.

Refusing redirects is sensible for credentialed APIs, but the resulting message does not explain the wrong origin/path or redirect location safely. An HTTP-to-HTTPS or auth-gateway redirect is not a working direct API path.

**Proposed repair:** explicitly validate/document whether base-path deployment is supported. For the current root-mounted setup, reject UI/API paths early with a helpful message; surface redirects as a canonical-host/proxy issue. Do not blindly follow cross-origin redirects carrying instance keys.

**Verification needed:** UI URL, `/api` URL, canonical origin, trailing slash and any intentionally supported prefix are tested against expected request paths. Proxy redirects are reported without credential disclosure.

## Additional source-backed setup/UI gaps

### Network sectors must be configured before approval

The Pair UI checks this before invite creation, and `approve_pairing()` calls `network_config.require_configured()`. Merely obtaining a token or opening the Pair page is not a complete setup. At least one permitted sector must be selected and saved, and approval's sectors must be an enabled subset. This is an omitted prerequisite in shorter instructions, not necessarily a backend defect.

### Browser copy still tells Lite users to visit an Outpost wizard

The [Pair page](../../../PLG_Ai_Interface/NewStatic/app/%28command%29/command/pair/page.tsx) labels clients as Lite/Outpost, but several main instructions and messages still say to paste the invite into Outpost `/setup/`. That is misleading for a terminal Lite user. Render per-client instructions or show the Lite terminal command alongside the Outpost steps.

### Status loads configuration that connect does not load

`connect` executes before normal bootstrap using `--command-url`. `command-status` calls bootstrap, which loads `.env`; `_sol_command_client()` rejects a `SOL_COMMAND_URL` inconsistent with the saved host. A stale override can make the verification command fail after pairing succeeded. The explicit connection argument and later override must agree; the terminal guide now calls this out.

### “Offline” is not necessarily broken Lite credentials

Lite has no background heartbeat loop in this client. The generic Command registry ages liveness based on heartbeat timestamps. The Lite status handler verifies credentials/type independently of that online/offline label. A valid Lite link can therefore appear offline in the fleet display. A separate Lite-aware liveness contract/UI is preferable to requiring the operator to re-pair because a heartbeat expired.

## Not established by this static review

No evidence here identifies the actual deployed URL, certificate, proxy rules, server mode/revision, running worker topology, attempted command, request status or registry state from the failed attempt. Local source is not a deployment audit. In particular, no pending entry can result from a chat command that never executed, unreachable/wrong API host, auth/proxy rejection, expired invite or a registration failure; the reported silence does not distinguish them.

The checked current client/server fields and response shape are compatible. There is no source-backed reason to require Lite to become a website or use the Outpost wizard. Fixing observability and recovery is necessary, but proving the user's live cause requires the narrow evidence described in the [operator runbook](../integrations/command-real-world-linking.md#8-nothing-appears-isolate-the-registration-stage).

## Suggested repair order for a later implementation task

1. Safe CLI progress with pending ID and stage-specific errors.
2. Canonical base URL validation and full pairing-state handling.
3. Keyring preflight plus explicit uncertain/lost-claim recovery design.
4. Actual client-to-Command contract tests for registration/approval/claim/storage/failure, not only separately mocked happy paths.
5. Lite-specific Pair UI instructions and liveness interpretation.

These are proposed changes, not changes made or verified in this documentation task. The existing unrelated source/test edits in the workspace were left untouched.
