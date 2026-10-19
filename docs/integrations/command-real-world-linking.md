# Link terminal SOL-Lite to SOL-Command: real-world operator guide

## Update: 19 October 2026 client repair

The updated client prompts securely when `--invite-code` is omitted, checks the OS keyring before submitting the invite, prints registration/wait/claim/storage progress, and identifies failed HTTP stages without printing secrets. Removed/expired requests stop immediately. Page URLs such as `/setup` are rejected; use the canonical Command HTTPS origin. The historical silence and generic-error descriptions below apply to older clients.

From PowerShell in the installed Lite folder, outside agent chat:

```powershell
.\.venv\Scripts\python.exe -m sol_lite connect --command-url https://YOUR_COMMAND_HOST --name 'Desk SOL-Lite'
# Paste the fresh Command invite at the hidden prompt, then keep this running.
# Administrator: approve the matching SOL-Lite client on Command's Pair page.
.\.venv\Scripts\python.exe -m sol_lite command-status
```

The same Command pairing invite supports both client types. Lite must register itself as `sol-lite`; an already-issued Outpost instance key is not an invite and cannot authenticate Lite APIs. Deploy the updated Lite client and rebuild/deploy Command's frontend to see the corrected operator instructions. These repairs were checked locally with mocked HTTP/keyring tests; a live host pairing still requires the real host, fresh invite and administrator approval.

Source checked on 17 October 2026 in both `PLG_Ai_Lite` and the neighbouring `PLG_Ai_Interface` Command checkout. No live host was probed and no pairing was attempted while writing this guide. Local source is not evidence that the deployed host runs the same version.

**SOL-Lite is a terminal application. It has no `/setup` webpage.** Only the Command administrator uses a browser. The Lite operator runs a shell subcommand, then waits while the administrator approves the registered client. Being a terminal app does not prevent its Python HTTP client calling Command.

The reported symptom is: no visible output/logs and no pending request visible in Command. Follow the stages below; do not assume registration succeeded or that the UI is simply slow. The [static logic analysis](../debugging/command-pairing-static-analysis.md) explains confirmed code gaps.

## 1. Get the correct server and administrator ready

The Command administrator must provide:

- The exact canonical **HTTPS base URL**, for example the organisation's configured `https://sol-command.corp.pacenlife.com`. Confirm this real hostname rather than assuming the example is reachable.
- A running Command hub backend, not an Outpost backend or only static frontend. The checked server enables hub behavior for `SOL_MODE=command` or `all`; `outpost` does not register the same hub route/auth path.
- A trusted TLS chain from the Lite PC, DNS/network access, and a reverse proxy routing both `/api/hub/` and `/api/lite/` to that backend.
- An authenticated Command administrator browser session, with network sectors configured and a fresh pairing invite ready.

Do not use a URL ending in `/command/pair/`, `/setup`, `/login`, `/api` or `/api/hub`. The client appends its own API paths. Do not use the Ollama URL or the disabled Lite bridge port. Do not turn off TLS verification, application authentication or invite requirements as a fix.

## 2. First prove the intended API is reachable — no credentials needed

The following commands are **for you to run** in normal PowerShell on the Lite computer. They do not pair or create a client. Replace the hostname with the administrator's actual canonical origin; no invite or key goes into these checks.

```powershell
$commandBase = 'https://sol-command.corp.pacenlife.com'
Resolve-DnsName ([uri]$commandBase).Host
Test-NetConnection -ComputerName ([uri]$commandBase).Host -Port 443
curl.exe --silent --show-error --max-time 15 --dump-header - "$commandBase/api/health"
curl.exe --silent --show-error --max-time 15 --dump-header - "$commandBase/api/lite/v1/status"
```

Expected interpretation:

- DNS failure or TCP failure: fix DNS/VPN/routing/firewall before pairing. TCP success alone does not prove HTTP/TLS/API health.
- `curl` certificate error: have the server/IT administrator fix hostname/certificate-chain trust for the client. Do not add `-k`.
- Health returns JSON: confirms a responder, not necessarily the correct Command deployment.
- Lite status returns **HTTP 403** and a JSON detail like `Invalid instance credentials`: expected without credentials, and evidence the Lite route is exposed through middleware/proxy to its credential check.
- Status returns **401**, a login redirect, HTML or access-gateway challenge: the request may be reaching user-session authentication or an upstream proxy instead of the instance-authenticated Lite route. The CLI sends no browser login cookie. Have the administrator check mode, deployed revision, middleware and proxy rules.
- Status returns **404**: wrong host/backend, missing Lite routes in deployed code, or proxy path routing. Do not start repeatedly consuming invites.
- **301/302/307/308**: the client does not follow redirects. Use the correct canonical HTTPS origin or have the proxy preserve the intended API route. Do not enable arbitrary redirects for requests containing credentials.

For a nonstandard explicit HTTPS port, use that port in the TCP check. The checked API expects no cookie on its machine-auth paths. This is not a request to make administrative invite/approve routes public.

## 3. Command administrator: configure sectors and create an invite

In the **Command browser**, sign in as an administrator and open the Pair page at:

```text
https://YOUR_COMMAND_HOST/command/pair/
```

Source UI labels for this checkout:

1. Under **1. Network sectors (mandatory)** select the intended sectors and click **Save network sectors**. Confirm the page reports configured. The server refuses approval if network configuration is absent.
2. Under **2. Create pairing invite**, choose at least one permitted sector and an optional useful name hint. Click **Create invite**.
3. Copy the **full invite code**, not a screenshot/URL/label. This server also supports its short display code, but using the full value avoids ambiguity and older-version differences.
4. Keep the page open, watching **3. Pending approvals**. Coordinate with the operator immediately: invites and pending tokens have a ten-minute lifetime in the checked source.

Some page text still says “Outpost” or directs users to `/setup/`. That text is for the web-based Outpost. **For Lite, the next step happens in PowerShell, not an Outpost setup page.** Lite registration supplies `client_type: sol-lite`; the invite itself is not a separate special Lite credential format.

## 4. Lite operator: run the connection command outside chat

In a normal PowerShell window, from the installed checkout:

```powershell
Set-Location "$env:USERPROFILE\PLG_Ai_Lite"
.\.venv\Scripts\python.exe -m sol_lite --help
```

Confirm `connect` appears in help. If currently inside the SOL-Lite agent chat, exit with `/quit` first or use a second normal PowerShell window. Do not paste the shell command as a chat message or type `/connect`; the slash dispatcher does not implement that command.

Enter the invite without placing its literal value directly in PowerShell command history:

```powershell
$commandBase = 'https://YOUR_COMMAND_HOST'
$liteInvite = Read-Host 'Paste the fresh full Command invite'
.\.venv\Scripts\python.exe -u -m sol_lite connect --command-url $commandBase --invite-code $liteInvite --name 'Desk SOL-Lite'
```

Replace the URL before running. The invite still becomes a child-process argument and can be visible to sufficiently privileged local process inspection; do not record the process arguments or share a terminal transcript containing it. No password or long-lived instance key belongs in the command.

**Current CLI silence is expected during its polling, but is not proof of progress.** It prints no registration/pending messages and no pending ID. `-u` cannot create messages the code never emits. Keep the command running while the administrator checks for registration. It polls roughly every three seconds, for up to ten minutes by default; an HTTP request can fail earlier.

## 5. Administrator: approve the matching pending request

On Command's Pair page:

1. Wait for its refresh (source polls every five seconds), then manually Refresh if needed.
2. Find `Desk SOL-Lite` and confirm the client label/type is **SOL-Lite**, not an unrelated Outpost.
3. Review its host hint and selected permitted sectors. Do not approve an unknown request just because it arrived at the same time.
4. Click **Approve** before expiry. Server approval consumes the invite. Keep the operator's CLI running: it still must claim and store credentials.

If nothing appears, use section 8. Do not create many simultaneous requests with one invite; a successful registration reserves that invite for its pending request.

## 6. Lite: confirm claim and storage, then live status

Success prints:

```text
Paired with SOL-Command as instance ...
Assigned sectors: ...
```

This occurs only after the response has been claimed and saved in the current user's OS keyring under provider `SOL-Lite`, entry `sol-command`. Then:

```powershell
$pairExit = $LASTEXITCODE
"pair exit=$pairExit"
$liteInvite = $null
.\.venv\Scripts\python.exe -m sol_lite command-status
```

A successful live status includes `ok: true`, the assigned `instance_id`, sector list and `lite_access`. Do not paste the keyring contents into reports. If the live command fails after CLI success, distinguish a wrong `.env`/process `SOL_COMMAND_URL`, a revoked credential, an unavailable route and wrong server from the original pairing stage.

`connect` uses its explicit URL before normal bootstrap. `command-status` loads bootstrap and its `.env`. Therefore a stale `SOL_COMMAND_URL` in `.env` or the process can break status even though the initial connection worked. It must match the paired host; remove/correct only the stale override deliberately. `SOL_INSTANCE_ID` and `SOL_INSTANCE_KEY` are rejected rather than being credential configuration.

## 7. Use the link from PA

Close/restart the agent shell after pairing. Select `/use sol_pa` and ask:

```text
After required approval, check SOL-Command status and report the assigned sectors and Lite grants without exposing credentials. Do not read sector contents, submit proposals or sync skills yet.
```

Only PA lists the Command tools. `sync-skills` is a separate shell command and stages packages for review; it does not activate them. Jarvis is separate administrator-granted access and creates pending proposals. The [integration reference](sol-lite.md) describes these limits.

A registry row can age to “offline” because Lite has no background heartbeat loop. That display alone does not prove credentials are invalid: verify `command-status`. The current Lite route verifies credentials/client type, not the heartbeat liveness label.

## 8. Nothing appears: isolate the registration stage

Do these checks in order:

1. **Was `connect` run in PowerShell?** The chat may treat pasted commands as text; it does not execute the CLI automatically. Confirm help and the actual `.venv` command above.
2. **Is the CLI still running or back at its prompt?** If back, record its exact final error and exit code. If running, note elapsed time; do not assume the invisible step completed.
3. **Do unauthenticated route probes behave as section 2 describes?** A browser page loading is not proof of API routing. Browser cookies cannot authenticate the standalone CLI.
4. **Is the administrator looking at the same host and a configured Pair page?** In browser Developer Tools → Network, inspect the UI's own `GET /api/hub/instances` response and its `pending` array. Record only safe names/client types/status, not raw invitation/token material. UI filters/cached deployments can differ from backend state.
5. **Server operator checks access/error logs for `/api/hub/pair/register`.** Use the actual deployment's container/service/proxy log viewer; this repository does not establish the running service name. Correlate timestamps and response status without logging request bodies. No request at proxy implies wrong client command/network/host; proxy sees it but application does not suggests routing/upstream issues. Application audit includes `pairing_registered` only after registration/reservation succeeds; absence alone does not prove no attempt reached the server.
6. **Registration returned 400?** Command's safe server detail can distinguish expired, used, reserved or missing invites. The current Lite CLI hides it behind a generic HTTP code. The admin should inspect the relevant server diagnostics, never request the secret request body.
7. **Pending exists but client timed out?** Current Lite does not persist the token/nonce for resumption. Have the administrator reject the stale pending row, or remove the intended abandoned approved instance if applicable, then create a fresh invite and coordinate another attempt.

Do not disable `AUTH_ENABLED`, `SOL_PAIRING_REQUIRE_INVITE` or TLS as troubleshooting shortcuts. Without HTTP error/status or deployment logs, a specific network or backend root cause remains unconfirmed.

## 9. Errors and safe recovery

- **HTTP 400 during registration:** fresh invite, correct full code, no competing request; admin checks actual detail and sector setup.
- **HTTP 401/login page/redirect:** confirm Command mode, deployed middleware/proxy exemptions and canonical API host. Pair register/status/claim are machine bootstrap endpoints; invite/approve remain administrator-only.
- **HTTP 403 at post-pair status:** invalid/revoked identity, wrong backend or old client type; compare the admin's instance type and intended host without copying keys.
- **HTTP 409 on claim:** client-type/claim-state mismatch or wrong deployed server revision; verify it supports `sol-lite`. The checked server intentionally bypasses Outpost product-version equality for a properly registered Lite claim.
- **HTTP 410 / already claimed, or keyring save failed after approval:** the server may have consumed the one-time claim before local storage failed. Fix the user's keyring first, have the admin retire the orphaned instance, and start with a new invite. No automatic resume/reclaim exists.
- **Timeout awaiting approval:** invite/pending expired, request rejected/unknown, wrong Pair page or approval not completed. Current client can label unknown/rejected situations as generic waiting; inspect server state.
- **Connection error naming only an exception type:** obtain stage/timestamp from server/proxy logs; the client currently suppresses detailed transport diagnostics. Do not post full secret-bearing URLs or enable raw HTTP body logging.

To disconnect a working local link, run `python -m sol_lite disconnect` using the app interpreter. This removes only the local keyring entry. The Command administrator separately deletes/revokes the intended instance. Do not erase a working pairing while investigating a different machine's failed attempt.

## 10. Completion record

Record: Lite commit/version, deployed Command commit/version if known, canonical host, route-probe HTTP statuses/content types, connect timestamp/exit, whether pending appeared, client type, approval/claim outcome, local storage success, and live `command-status` result. Keep invites, claim nonce, instance keys and raw keyring data out of the record.

For macOS replace the interpreter with `.venv/bin/python`; run the same shell subcommands in Terminal. Lite still has no setup website. For confirmed code findings and proposed repairs, read [pairing static analysis](../debugging/command-pairing-static-analysis.md).
