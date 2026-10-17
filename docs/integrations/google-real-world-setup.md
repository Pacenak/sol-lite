# Real-world Gmail and Google Calendar setup for SOL-Lite

Checked against SOL-Lite source and official Google documentation on 17 October 2026. This chapter provides instructions for you to perform; no account was connected while writing it. It covers the existing Gmail/Calendar integration, not Google Docs or Drive authoring.

Use a normal Windows PowerShell window. The same computer must run the CLI and receive the browser's local OAuth callback. Administrator PowerShell is not required. Complete the base Python installation first.

## 1. Know what the two Google accounts/roles mean

The person configuring Google Cloud needs permission to create/configure a project and its OAuth client. The person authorizing SOL-Lite needs a Google account with Gmail and Calendar enabled. They can be the same person. A managed company account may additionally need Workspace administrator approval; local Windows elevation cannot grant Google permissions.

For an initial personal/test setup this guide uses an **External** app in **Testing** with your exact account added as a test user. Organisation-only production deployments should have their administrator choose and approve the appropriate audience instead. [Google's audience documentation](https://support.google.com/cloud/answer/15549945).

## 2. Create and select one Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/) in your browser and sign in as the project owner/operator.
2. Use the project selector at the top, choose **New project**, name it `SOL-Lite Personal`, choose an organisation/location if your account requires one, and create it.
3. Select that new project after creation. Keep using this same project for both APIs, consent and the OAuth client.
4. If project creation is forbidden, ask your Cloud administrator to create/assign a project. Do not create credentials in an unrelated company project.

Google's [project creation instructions](https://developers.google.com/workspace/guides/create-project) explain the required project access.

## 3. Enable both APIs in that project

Open **APIs & Services → Library**. Search for **Gmail API**, open its API page and choose **Enable**. Return to Library and enable **Google Calendar API**. Confirm both appear under enabled APIs for the selected project. An API enabled in another project does not enable this client's project.

Official setup references: [Gmail Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python) and [Calendar Python quickstart](https://developers.google.com/workspace/calendar/api/quickstart/python). Follow their Cloud setup concepts; use SOL-Lite's connection command below rather than installing/running a separate quickstart application.

## 4. Configure the consent identity and test user

1. Open **Google Auth platform → Branding**. If not configured, choose **Get started**.
2. Set app name `SOL-Lite Personal`, your real support email and developer/contact email. Review the policy and complete creation.
3. Open **Audience**, choose **External** for this personal/test path, and keep publishing status **Testing**.
4. Under **Test users**, add the exact Gmail/Workspace email address you will choose in the authorization browser. Save.
5. A Workspace-owned project may offer **Internal**, restricted to its organisation. Do not use that audience for a personal account outside it.

Menu presentation can change; the authoritative reference is [Configure OAuth consent and scopes](https://developers.google.com/workspace/guides/configure-oauth-consent). If your organisation blocks the app, its administrator must evaluate the requested client/scopes; do not bypass its account controls.

## 5. Declare the scopes the code actually requests

Under **Google Auth platform → Data Access**, add these three scopes and save:

```text
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/calendar.events.owned
```

They are defined in `src/sol_lite/integrations/google_workspace.py`. Gmail read is restricted and Gmail send is sensitive in Google's scope classification; distributing the application can require verification and other review. Do not add full Gmail/Drive access as a troubleshooting shortcut. [Gmail scope definitions](https://developers.google.com/workspace/gmail/api/auth/scopes).

The current code requests all three together, even if your first test only reads. The application has its own per-operation approvals, but that does not narrow the Google OAuth consent grant. Calendar use is limited by this scope and the implementation's primary-calendar operations.

## 6. Create the correct client and download its JSON

1. In the same project open **Google Auth platform → Clients**.
2. Choose **Create client**, application type **Desktop app**.
3. Name it `SOL-Lite Desktop` and create it.
4. Download the client's JSON using the download action on its details/list entry.
5. Do not choose Web application, API key or service account. SOL-Lite uses `InstalledAppFlow.from_client_secrets_file`, not those authentication flows.

Google's [desktop OAuth guide](https://developers.google.com/identity/protocols/oauth2/native-app) documents the installed-app flow. If the console offers an AI-agent classification field, review its meaning with the project owner and current Google guidance; this repository does not demonstrate special support for a new Google agent-specific OAuth extension.

Save the downloaded file outside Git and outside the agent's working files. In File Explorer create `%USERPROFILE%\Secrets\SOL-Lite`, move the download there and rename it `google-desktop.json`. Enable file extensions and ensure it is not `google-desktop.json.txt`.

The official quickstarts use a local `credentials.json` and separate `token.json`; SOL-Lite instead takes the explicit JSON path and stores authorization tokens in the OS keyring. Do not copy quickstart token-file instructions into this setup.

## 7. Install the extra and connect from the terminal

Run in normal PowerShell, from your SOL-Lite checkout. These commands deliberately install packages/connect the account when you execute them:

```powershell
Set-Location "$env:USERPROFILE\PLG_Ai_Lite"
.\.venv\Scripts\python.exe -m pip install -e ".[google]"
Test-Path "$env:USERPROFILE\Secrets\SOL-Lite\google-desktop.json"
```

The last command must print `True`. Then:

```powershell
.\.venv\Scripts\python.exe -m sol_lite google-connect --client-secrets "$env:USERPROFILE\Secrets\SOL-Lite\google-desktop.json"
```

Keep PowerShell open. A browser opens; choose the account added as a test user, verify the project/app identity, inspect the requested permissions and authorize your intended app. An unverified-app warning in your own controlled test project is different from an account administrator denying access; stop for unexpected project identities or account policy blocks.

Expected browser success text from this source:

```text
Google is connected to SOL-Lite. You may close this tab.
```

Expected CLI success:

```text
Google Workspace connected. SOL-Lite stores the authorization in the OS keyring.
```

The listener binds `127.0.0.1` on an automatically selected free port (`port=0`). Do not enter `8787`, an Ollama port or a Command URL as a Google redirect. Do not run the CLI through SSH on another computer while authorizing the callback on your own laptop. No publicly exposed listener is required.

The JSON path argument avoids an implementation trap: `google-connect` is handled before normal bootstrap loads the repository `.env`. Putting `SOL_GOOGLE_OAUTH_CLIENT_SECRETS` only in `.env` is therefore insufficient for that CLI path. An actual process environment variable works, but the explicit argument is clearer.

## 8. Verify saved authorization, then actual access

```powershell
.\.venv\Scripts\python.exe -m sol_lite google-status
```

This checks saved authorization, not a successful Gmail/Calendar request. Close/restart the interactive app so bootstrap constructs its connected client. Select `/use sol_pa` and send one prompt at a time:

```text
After the required private-data approval, use Gmail search with the exact query newer_than:1d and return at most one matching message's subject/date. Do not send, forward, modify messages or create events. If none match, report the actual empty result.
```

Then replace the example interval with your desired future interval and explicit UTC offsets:

```text
After the required approval, list my primary-calendar events from 2026-10-19T09:00:00+13:00 to 2026-10-19T17:00:00+13:00. Report the actual result, including an empty result. Do not create or change events or invite anyone.
```

These dates are an example in Auckland daylight time, not a recurring setting. Only approved successful tool results establish access. Do not send a test email or create an event unless you separately intend that write and review its full recipient/body/time details.

## 9. Real-world failures and exact next checks

- **`Google OAuth client JSON was not found`:** check the exact path with `Test-Path`, filename extension and explicit `--client-secrets` argument.
- **Missing optional dependencies:** install `.[google]` using the same `.venv` interpreter that starts the application.
- **`access_denied`, app still being tested:** verify the exact authorized account is listed under Audience → Test users in the same project. A company policy block needs its Workspace administrator.
- **`org_internal`:** the chosen account is outside the project's Internal audience. Use the project owner's intended audience/account; do not assume a personal account belongs to the company organisation.
- **`redirect_uri_mismatch`:** confirm the JSON belongs to a Desktop app. Re-download the correct client JSON and reconnect rather than configuring a random fixed web callback.
- **API disabled / `accessNotConfigured` / `SERVICE_DISABLED`:** enable the specifically named API in the OAuth client's project and allow the service configuration to propagate.
- **`invalid_grant` after previously working:** revoke/re-consent as appropriate. External Testing grants with these scopes can expire after seven days. Production distribution requires an intentional publishing/verification decision, not just toggling a setting. [Google refresh-token expiration rules](https://developers.google.com/identity/protocols/oauth2#expiration).
- **Saved status passes but tool says disconnected:** restart chat and recheck the normal user's keyring context. A client already constructed before connection does not automatically become connected.
- **Consent finishes but CLI reports keyring failure:** authorization is not safely saved until the keyring write succeeds. Resolve the normal user's credential-store problem and reconnect; do not put tokens into chat/YAML as a workaround.

For scope changes or a different account:

```powershell
.\.venv\Scripts\python.exe -m sol_lite google-disconnect
.\.venv\Scripts\python.exe -m sol_lite google-connect --client-secrets "$env:USERPROFILE\Secrets\SOL-Lite\google-desktop.json"
```

Google account-side revocation is separate from removing Lite's local keyring entry. See [Google account third-party access](https://myaccount.google.com/connections).

## 10. Record the result without recording secrets

Record project display name/ID, Desktop client type, audience/status, enabled APIs, allowed test account (redact in shared reports), connection success/failure and outcomes of both approved read tests. Do not include client JSON contents, authorization URLs/codes, tokens or private email bodies.

The code refreshes credentials lazily during API calls. There is no background inbox monitoring, Google Docs/Drive integration or general account-sync service implemented by this Gmail/Calendar adapter. For all local system prerequisites return to [the operator runbook](../getting-started/zero-to-battle-noob-runbook.md).
