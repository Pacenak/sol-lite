# Google Workspace for SOL-Lite PA

Google Workspace is the first external email and calendar provider supported by SOL-Lite. Provider-specific API calls live behind `GoogleWorkspaceClient` so later providers can implement the same PA capabilities without changing the agent tools.

## Setup

1. In Google Cloud Console, create a project and enable the Gmail API and Google Calendar API.
2. Configure the OAuth consent screen and create an OAuth client of type **Desktop app**. Download its client JSON.
3. Install the optional Google dependencies: `pip install -e ".[google]"`.
4. Set `SOL_GOOGLE_OAUTH_CLIENT_SECRETS` to the downloaded JSON path, then run `sol-lite google-connect`. SOL-Lite opens the system browser for Google consent and receives the response on a loopback listener.
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
