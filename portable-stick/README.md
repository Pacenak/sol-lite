# Portable Studio Admin Tool Belt (500 GB M.2)

Dual-mode USB3 NVMe for the **studio owner**: personal SOL-Lite + admin cheatsheets + SecCheck / lite-pen (authorized lab) + pouch hardware docs.

- **Full setup (gapless):** [docs/user/admin-toolbelt-full-setup.md](../docs/user/admin-toolbelt-full-setup.md)
- **Day-1 short:** [docs/user/dummies-admin-stick-m2.md](../docs/user/dummies-admin-stick-m2.md)
- **Design:** [admin-toolbelt-full-setup-design](../docs/superpowers/specs/2026-10-13-admin-toolbelt-full-setup-design.md)
- **Plan:** [admin-toolbelt-full-setup plan](../docs/superpowers/plans/2026-10-13-admin-toolbelt-full-setup.md)

## 500 GB budget (3 partitions)

| Slice | Size | Role |
|-------|------|------|
| `SOLBOOT` | ~96 GB | Ubuntu LTS Helper + GRUB SecCheck / Lab-pen |
| `SOLLITE` | ~64 GB exFAT | Lite git clone + venv — **no secrets** |
| `SOLBRAIN` free reserve | ~20 GB | Leave empty |
| `models/` on BRAIN | ≤80 GB | Small GGUFs only |
| `SOLBRAIN` rest | ~320 GB+ | Encrypted `data/`, workspace, admin-belt, sec reports |

Encrypt **SOLBRAIN**. Apple Silicon Macs: **Carry only** (no USB Helper boot).

## Partitions

| Label | FS | Contents |
|-------|-----|----------|
| `SOLBOOT` | EFI + ext4 | [boot/README.md](boot/README.md) |
| `SOLLITE` | exFAT | [lite/README.md](lite/README.md) |
| `SOLBRAIN` | encrypted | Copy of [brain/](brain/) from this tree |

## Pouch (physical)

[pouch/README.md](pouch/README.md) — ATHEN female NIC, Lenovo USB-C 2.5G, RJ45 male, Huawei E3531 (OOB cell), Vodafone R209 (lab MiFi).

## Personalities

| Mode | How | What |
|------|-----|------|
| **Carry** | Host OS → mount LITE + BRAIN | Launchers on BRAIN; `SOL_LITE_REPO` → SOLLITE |
| **Boot → Helper** | UEFI USB boot Ubuntu | Same Carry paths |
| **Boot → SecCheck** | GRUB / Ventoy | [boot/seccheck](boot/seccheck/README.md) |
| **Boot → Lite pen** | Lab-pen entry | [boot/lab-pen](boot/lab-pen/README.md) |

## Carry-mode quick start

1. Mount **SOLLITE** + unlock **SOLBRAIN**.
2. `brain/launch/Launch-SOL-Lite.ps1` or `.sh` (from BRAIN).
3. Admin index: [brain/admin-belt/README.md](brain/admin-belt/README.md).
4. Sec: copy `brain/sec/*.example` → live files; unlock admin agent.
5. Stop + safely remove.

## Not on this stick

- Studio Outpost product clone as SoT  
- Command pair secrets in plaintext  
- Auto-scan of the internet / third-party nets  
- Exploit payloads in git  
- Mac USB-boot of Helper/SecCheck/Lab-pen  
