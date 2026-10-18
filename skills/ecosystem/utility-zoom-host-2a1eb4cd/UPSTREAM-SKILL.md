---
name: zoom-host
description: "Create client Zoom meetings on the Pro (tefggl) as a shared host server — no extra seats. Public join_url for clients; facilitator fetches start_url near start via Credential Gateway. Triggers: create zoom meeting, заведи зум, invite to zoom, host link, zoom для клиента."
---

# zoom-host — shared Zoom Pro host server

Use Greg’s Zoom Pro (`your-account@gmail.com`) as a **team host server** without buying Licensed seats.

Canonical product docs: private repo `your-zoom-proxy`.  
Execution plane: Credential Gateway capabilities `zoom.meeting.*` (adapters in `your-credential-gateway`).  
Architecture gate: `the architecture doc`.  
Account bootstrap: `your-zoom-proxy` → `docs/ZOOM_ACCOUNT_HOST_SERVER.md`.

## When to use

- MM asks to create a Zoom for a client at a specific time and invite emails.
- Need join link for clients + host start link for the facilitator (Kristina, etc.).
- Cloud recording must land on tefggl (existing zoom→YT→Notion).
- «Дошло ли приглашение?» → scoped `gmail.zoom-invite.check` (verification mailbox only).

## When NOT to use

- Webinar-hardened Greg-only webinars (waiting room ON) → old runbook profile.
- Manual recording download → `scripts/zoom_download_recording.mjs`.
- Giving anyone Zoom S2S secrets.
- Full Gmail search / mailbox dump — **forbidden**; only meeting-scoped invite check.

## Security (non-negotiable)

| Pack | Contents | Who |
|---|---|---|
| **Public** | topic, time, `join_url`, meeting id, passcode | Clients / invitees |
| **Host** | `start_url`, `dynamic_host_key` | Facilitator only via `zoom.meeting.get-host-link` |

- Never put `start_url` in client email, ICS, Notion, Telegram to clients.
- `start_url` expires ~2 hours — create early, **get-host-link near start**.
- Pro = **1 concurrent meeting** — always `check-slot` first.
- Invite delivery check reads **only** Zoom-invite mail for a `meeting_id` in the gateway verification mailbox (`your-account@gmail.com`). Cannot confirm other inboxes unless that address was invited as canary or OAuth for that mailbox is added.

## Agent workflow

1. Parse topic, `start_time` (ISO UTC or with timezone), duration (default 60), invitee emails.
2. If the user names a client without email → `notion.crm.contacts.lookup` / CLI `lookup --query` on CRM «Контакты контрагентов» (filtered Notion query, no full dump).
3. `zoom.meeting.check-slot` — if `available: false`, tell MM who/what overlaps; do not create unless they insist with `force_overlap` (warn hard).
4. `zoom.meeting.create` with idempotency key — show **public** pack only + hint to fetch host link later.
5. Optionally draft client invite text from public pack (join_url only).
6. When MM is about to start: `zoom.meeting.get-host-link` — show host pack privately; instruct: open `start_url` → you are host → Make Co-Host for others if needed → confirm cloud recording.
7. Optional delivery proof: `gmail.zoom-invite.check` / CLI `check-invite --meeting-id …` (only verification mailbox).
8. Cancel: `zoom.meeting.cancel`.

## Client (CLI)

From `your-zoom-proxy`:

```bash
export ZOOM_HOST_GATEWAY_URL='https://credential-gateway-staging.up.railway.app'
# bearer in ~/.config/hwai-zoom-host/bearer (chmod 600)
node scripts/zoom-host-client.mjs lookup --query 'Victor'
node scripts/zoom-host-client.mjs create --topic 'X <> Client' --start-time '2026-07-30T12:00:00.000Z' --invite a@b.com
node scripts/zoom-host-client.mjs get-host-link --meeting-id 123
node scripts/zoom-host-client.mjs check-invite --meeting-id 123
```

Team onboarding: `docs/TEAM_ONBOARDING.md` + Claude setup prompt: `docs/CLAUDE_CODE_SETUP_PROMPT.md`.

## Meeting defaults (shared_host_no_seats)

`join_before_host: true`, `jbh_time: 0`, `waiting_room: false`, `auto_recording: cloud`, no `alternative_hosts`.

## Related

- Runbook dual profiles: `the runbook`
- Recording → YT: `scripts/n8n_zoom_recording_to_youtube_blueprint.md`
