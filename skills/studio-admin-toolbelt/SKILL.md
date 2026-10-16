---
name: studio-admin-toolbelt
description: >
  Guide the studio owner portable M.2 admin tool belt — SOLBOOT/SOLLITE/SOLBRAIN
  partitions, Carry vs UEFI Boot, pouch NICs and cellular (ATHEN, Lenovo 2.5G,
  E3531 OOB, R209 lab MiFi), SecCheck/lite-pen allowlists, and sol_studio_admin
  unlock. Owner-authorized lab only; skills never grant tools or permissions.
---

# Studio admin tool belt

Use when the operator asks about the admin stick, pouch adapters, SecCheck, lite pen, SOLBRAIN/SOLLITE, Helper Ubuntu, or `sol_studio_admin`.

## Evidence first

1. Prefer these in-repo paths (adjust if Carry mounts differ):
   - `docs/user/admin-toolbelt-full-setup.md` — gapless setup
   - `docs/user/dummies-admin-stick-m2.md` — day-1 short
   - `portable-stick/README.md` — template overview
   - `portable-stick/pouch/` — hardware cards
   - `portable-stick/brain/admin-belt/` — ops cheatsheets
   - `portable-stick/brain/sec/` — allowlist + runners
2. Use workspace/file tools to open those docs when the workspace is the Lite repo or BRAIN copy.
3. Run `studio_owner_status` before promising the admin agent is available.

## Partitions (correct mental model)

| Volume | Role |
|--------|------|
| `SOLBOOT` | Ubuntu LTS Helper — UEFI PC boot only |
| `SOLLITE` | Lite git clone — no secrets |
| `SOLBRAIN` | Encrypted `data/`, admin-belt, sec, reports |

Launchers live on BRAIN; `SOL_LITE_REPO` points at SOLLITE.

## Mac / Apple Silicon

Carry only. Do not instruct USB-boot of Helper/SecCheck/Lab-pen on Apple Silicon.

## Pouch roles

| Device | Use |
|--------|-----|
| ATHEN USB→RJ45 female | Studio LAN or Pi + patch |
| Lenovo USB-C 2.5G | Preferred fast NIC on USB-C hosts |
| USB→RJ45 male | Wall/switch jack |
| Huawei E3531 | **3G only** — dead for NZ/AU live OOB after 3G sunset; replace with 4G/5G — `portable-stick/pouch/huawei-e3531-full-setup.md` |
| R209 → SOL-LAB-MIFI | Offline Wi‑Fi bubble (no SIM); soft-mod + AI assist only — `portable-stick/pouch/sol-lab-mifi-offline-bubble.md`, `sol-lab-mifi-soft-modders.md` |

## SecCheck / lite-pen

1. Confirm `hosts.allow` lists **owned** hosts only.
2. Lite-pen needs `I_OWN_THIS_LAB` + unlock.
3. Call `studio_seccheck` / `studio_lite_pen`; quote `workspace/sec-reports/` paths.
4. Never invent scan results.

## Git / Outpost

Inspect with repository status/diff/log tools if needed. Push, merge, and `sol-git-upgrade` stay on the **host** with explicit Yes — remind, do not auto-push.

## Hard stops

- No third-party networks.
- No exploits or credential attacks.
- Skills do not unlock the admin agent or grant NETWORK/filesystem rights.
