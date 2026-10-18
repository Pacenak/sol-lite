---
name: n8n-temp-cleanup
description: >
  Discover and delete temporary / one-shot / exploratory n8n workflows in a
  single command. n8n requires archive-before-delete (REST API, cookie-auth);
  this skill wraps scripts/n8n_delete_workflow.mjs which handles the full
  deactivate → archive → delete lifecycle automatically. Use when the says
  "cleanup temp workflows", "delete temp n8n", "почисти temp", "удали
  временные воркфлоу", "n8n hygiene", "one-shot cleanup", or after creating
  and running a TEMP workflow that should not persist. Proactive — call THIS
  after any session that created temporary n8n workflows for testing.
allowed-tools: [Bash, Read]
---

# n8n TEMP workflow cleanup

Discover and delete temporary / one-shot / exploratory n8n workflows.

## Why this exists

n8n workflows accumulate silently. A session creates a TEMP workflow to test
a Gmail query, a Drive upload, or a Zoho read — runs it once, then leaves it.
After 3 months: 91 stale workflows cluttering n8n, 76 sharing the same Zoho
credential, nobody knows which are safe to delete (origin: 2026-08-12, 428 →
337 cleanup). The rule `n8n-one-shot-workflow-must-be-deleted.md`
mandates same-session deletion; this skill is the mechanical enforcement.

## n8n deletion lifecycle (archive-before-delete)

n8n does NOT allow direct deletion of an active, non-archived workflow:

```
DELETE /api/v1/workflows/:id  →  403 Forbidden (public API)
DELETE /rest/workflows/:id    →  400 "Workflow must be archived before it can be deleted"
```

Correct 3-step flow (REST API, cookie-auth):

1. **Deactivate** (if active): `POST /rest/workflows/:id/deactivate`
2. **Archive** (required): `POST /rest/workflows/:id/archive` → sets `isArchived: true`
3. **Delete** (permanent): `DELETE /rest/workflows/:id`

The script `scripts/n8n_delete_workflow.mjs` handles all 3 steps + credential
lookup via credentials-mcp automatically.

## Commands

### Auto-discover + delete all TEMP-named workflows

```bash
# Dry run — list all TEMP-named workflows (no changes)
node scripts/n8n_delete_workflow.mjs --temp

# Delete all TEMP-named workflows (deactivate → archive → delete each)
node scripts/n8n_delete_workflow.mjs --temp --force
```

`--temp` matches workflow names containing: `TEMP`, `TMP`, `temp`, `tmp`,
`_temp_`, `_tmp_` (case-insensitive). Safety guard: workflows with schedule
triggers, webhook triggers, or cron triggers are NEVER auto-deleted even if
their name contains "temp".

### Delete a specific workflow by ID

```bash
# Dry run — show what would be deleted
node scripts/n8n_delete_workflow.mjs <workflow-id>

# Confirm and delete
node scripts/n8n_delete_workflow.mjs <workflow-id> --force
```

### Batch delete from a file

```bash
# File: one ID per line (or comma/space separated)
node scripts/n8n_delete_workflow.mjs --batch <ids-file> --force
```

### List all stale workflows (broader than TEMP)

```bash
# Lists all inactive workflows without schedule/webhook triggers
node scripts/n8n_delete_workflow.mjs --list
```

## When to use

- **After creating a TEMP workflow** for testing a Gmail query, Drive upload,
  Zoho read, or any one-shot probe — delete it in the SAME session.
- **When the asks for n8n hygiene** — "почисти temp", "cleanup temp
  workflows", "удали временные".
- **Periodic sweep** — quarterly or when workflow count exceeds 400.
- **After a workflow is superseded** — deploy the new one, deactivate the old,
  delete after one verification cycle.

## When NOT to use

- Active scheduled workflows (4h, daily, weekly) — even if rarely triggered.
- Webhook-triggered workflows serving live integrations.
- Sub-workflows called by other active workflows.
- Workflows in a documented "standby" state with a reactivation plan.

## Output format

The script prints per-workflow progress:

```
[abc123]
  Workflow: TEMP — Check Exafunction in Drive [abc123] active=false
  ✓ Archived
  ✓ Deleted

Done: 17 deleted, 0 failed
```

On failure, exits with code 2 and prints failure reasons.

## Credentials

Reads from `your credentials config` via `your credentials tool`:
- `N8N_BASE_URL`
- `N8N_LOGIN_EMAIL`
- `N8N_LOGIN_PASSWORD`
- `N8N_API_KEY` (for API v1 reads, not used for delete)

Falls back to direct file parsing if credentials-mcp is unavailable.

## Composes with

- `n8n-one-shot-workflow-must-be-deleted.md` — the rule this skill enforces
- `close-task` — full task closure includes n8n temp cleanup
- `no-phantom-watchers.md` — sibling discipline (don't leave dangling automation)
- `prod-deploy-default.md` — finish what you start in the same session

## Origin

2026-08-19: after testing the Exafunction/Devin receipt pipeline, 3 temp
workflows were left in n8n (TEMP — Check Mark Bondarev labels, TEMP — Check
Exafunction in Drive, TEMP — List Exafunction Drive v2). the asked to
automate cleanup. The `--temp` auto-discovery mode was added to the existing
`n8n_delete_workflow.mjs` script (which already handled the archive-before-delete
lifecycle), and this skill was created for cross-IDE discoverability.
