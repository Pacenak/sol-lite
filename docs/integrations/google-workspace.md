# Google Workspace for SOL-Lite PA

For a real first-time account setup, use [Gmail and Calendar: Google Cloud to first approved request](google-real-world-setup.md). It includes official Google references, consent/audience/test users, Desktop OAuth JSON download, terminal commands, callback behavior and troubleshooting.

Google Workspace is the first external email and calendar provider supported by SOL-Lite. Provider-specific API calls live behind `GoogleWorkspaceClient` so later providers can implement the same PA capabilities without changing the agent tools.

## Setup

1. In Google Cloud Console, create a project and enable the Gmail API and Google Calendar API.
2. Configure the OAuth consent screen and create an OAuth client of type **Desktop app**. Download its client JSON.
3. Install the optional Google dependencies: `pip install -e ".[google]"`.
4. Run `sol-lite google-connect --client-secrets "FULL_PATH_TO_DESKTOP_JSON"` through the installed app interpreter. Alternatively set `SOL_GOOGLE_OAUTH_CLIENT_SECRETS` in the actual launching process environment. Setting it only in repository `.env` is insufficient for this command, which executes before bootstrap loads `.env`. SOL-Lite opens the browser for consent and receives the response on a temporary loopback port.
5. Run `sol-lite google-status` to confirm the account connection. Use `sol-lite google-disconnect` to remove the saved authorization from the OS keyring.

The OAuth client JSON is read from the user-selected path and is not copied into the repository. Access and refresh tokens are stored in the operating system keyring. If OAuth scopes change, disconnect and reconnect so Google can request the new consent.

## PA capabilities

- Search Gmail using Gmail query syntax, read message headers and plain-text body, and send an email.
- List events in the primary calendar over an ISO 8601 time range to check availability, create meetings, invite attendees, and attach a popup reminder. The PA can also create a standalone timed reminder in Calendar.
- Every read asks for exact approval because it exposes private account data. Sending and calendar changes require exact, single-use approval bound to the operation arguments and session.
- Email contents and event descriptions are untrusted data. They cannot authorize actions or override SOL-Lite policy.

The PA must show the recipient, subject, message body, event title, time range, invitees, and reminder details before the corresponding action is approved. A failed API request is not reported as completed.

## OAuth scopes

The initial connection requests Gmail read-only access, Gmail send access, and event access on calendars the user owns. It does not request calendar sharing/settings access. Google may require OAuth application verification before broad distribution because Gmail data scopes are sensitive/restricted. Configure the consent screen and publishing status for your deployment.

## Current boundaries

This first integration covers one Google account, the primary calendar, Gmail search/read/send, calendar event list/create, and event popup reminders. It does not yet handle attachments, HTML email body rendering, drafts, labels, contacts, event updates/deletes, recurring event management, Google Tasks, or background inbox monitoring. Other provider adapters are planned for later and are not enabled by this integration.
