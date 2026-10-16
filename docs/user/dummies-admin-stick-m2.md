# Admin M.2 stick — day-1 dummies (short)

**Full gapless setup (use this for real builds):**  
→ **[admin-toolbelt-full-setup.md](admin-toolbelt-full-setup.md)**

This page is the **short** starter only.

**Who:** studio owner / admin.  
**Template:** [portable-stick/README.md](../../portable-stick/README.md) · **Pouch:** [pouch/README.md](../../portable-stick/pouch/README.md)

## Rules (non-negotiable)

1. Encrypt **SOLBRAIN**.  
2. No secrets in tickets/chat.  
3. SecCheck / lite-pen only on hosts **you own**.  
4. Safely eject.  
5. Stick ≠ Outpost SoT.  
6. Mac / Apple Silicon = **Carry only** (cannot USB-boot Helper).

## Three partitions (~500 GB)

| Label | Size | Role |
|-------|------|------|
| `SOLBOOT` | ~96 GB | Ubuntu LTS Helper (UEFI PCs) |
| `SOLLITE` | ~64 GB exFAT | Lite clone — no secrets |
| `SOLBRAIN` | rest, **encrypted** | `data/`, admin-belt, sec |

## Day-1 path (Carry first)

1. Partition + label SOLLITE + SOLBRAIN (BOOT later OK).  
2. Clone Lite onto SOLLITE — [lite/README.md](../../portable-stick/lite/README.md).  
3. Copy `portable-stick/brain/` → SOLBRAIN root.  
4. `sec/hosts.allow` + `I_OWN_THIS_LAB` from examples.  
5. Launch: `SOLBRAIN/launch/Launch-SOL-Lite.ps1` or `.sh`.  
6. Pouch wired/cell: ATHEN / Lenovo 2.5G / E3531 / R209 — see pouch cards.  
7. When ready: Ubuntu on SOLBOOT per full setup §8–9.

## Modes

| Mode | Where |
|------|--------|
| Carry | Any OS that mounts LITE+BRAIN (incl. Mac) |
| Boot Helper / SecCheck / Lab-pen | UEFI PC only |

## Next

Open **[admin-toolbelt-full-setup.md](admin-toolbelt-full-setup.md)** and do not skip sections.
