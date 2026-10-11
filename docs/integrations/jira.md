# Jira for SOL-Lite

SOL-Lite stores one or more Jira Cloud connections for the PA and Engineer. Each connection names the project keys those agents may use. API tokens stay in the operating system keyring and never appear in tool results or prompts.

## Connect

```text
sol-lite jira-connect
```

The command asks for a connection name, the site URL (`https://example.atlassian.net`), the Atlassian account email, the API token, and the project keys for that site. `SOL_JIRA_API_TOKEN` can supply the token for a non-interactive run. The same screen is under Settings, option J. The token is not printed.

Check a live connection with `sol-lite jira-status`. Remove one connection and its token with `sol-lite jira-disconnect --name <name>`.

`sol-lite doctor` reports whether a connection is saved. It does not call Jira. `jira-status` is the network probe.

## What the agents can do

The PA can plan across every granted board with `jira_plan`, and can create, update, comment on, and transition issues inside those projects. The Engineer can read the same boards and issues, and can update, comment, and transition them. Neither agent can delete issues or assign them.

Searches are forced to `project in (GRANTED KEYS)`. An issue key whose project was not granted is rejected before Jira is called. If two sites are connected, a search has to name the project. Issue text is untrusted data. Reads need approval. Writes need exact approval, and a write is not done until the tool succeeds.

## Boundaries

This is Jira Cloud with an email and API token. It is not a connection to SOL-Full's integration store. Business does not receive these tools.
