# Admin-only agent: `sol_studio_admin`

This is an **admin-only feature** — not part of normal PA / engineer use.

## Double gate

| Gate | How |
|------|-----|
| Feature flag | `features.studio_admin` (default **off** in repo) **or** `SOL_STUDIO_ADMIN_FEATURE=1` |
| Personal unlock | `sec/I_OWN_THIS_LAB` (or `data/state/studio_owner.unlock`) with `I OWN THIS LAB` + your `owner_id:` |

Stick launcher turns **both** on when the unlock file exists on **your** BRAIN.

## Setup (you only)

1. `cp sec/I_OWN_THIS_LAB.example sec/I_OWN_THIS_LAB`
2. Set `owner_id: your-handle`
3. Launch via stick scripts → start Lite → switch to **SOL Studio Admin**
4. Without your stick unlock, cloning the repo alone never shows this agent

## Skill

Builtin **`studio-admin-toolbelt`** — stick partitions, pouch roles, SecCheck/Lab-pen, Mac Carry facts. Skills never grant tools or unlock.

## Tools (admin allowlist)

| Group | Tools |
|-------|--------|
| Unlock / sec | `studio_owner_status`, `studio_seccheck`, `studio_lite_pen` |
| Stick / docs | workspace inventory/list/find/read/search, notes, write/edit workspace files, `analyze_architecture_drift` |
| Host inspect | `execute_terminal_command`, `runtime_get_context`, `remote_list_nodes` |
| Git **read** | `repository_status`, `repository_diff`, `repository_log`, `repository_branches`, `repository_remotes` |
| Skills / procedures | `skill_discover`, `skill_install`, `procedure_*` |

**Not on this agent:** `repository_push`, hosting PR merge/create — use host Outpost / project-git with Yes.

Full setup: [admin-toolbelt-full-setup.md](../../../../docs/user/admin-toolbelt-full-setup.md) · Pouch: [../../pouch/README.md](../../pouch/README.md)
