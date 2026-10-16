# BOOT partition — Ubuntu LTS Helper (HUMAN-OPS)

Repo does **not** ship OS ISOs. Prefer **Ubuntu 24.04 LTS** installed onto `SOLBOOT` (~96 GB).

Full runbook: [docs/user/admin-toolbelt-full-setup.md](../../docs/user/admin-toolbelt-full-setup.md).

## Layout on ~96 GB BOOT

1. EFI + Ubuntu root for **Helper** (default boot).
2. Optional: second/third GRUB entries for **SecCheck** and **Lab-pen**, or Ventoy slot.
3. fstab: mount `SOLLITE` (exFAT) and `SOLBRAIN` (after unlock) for Helper. SecCheck/lite-pen need BRAIN at least for `sec/` + `workspace/sec-reports/`.

## Profiles

| Profile | Doc |
|---------|-----|
| Helper (Lite) | Mount LITE + BRAIN → `launch/Launch-SOL-Lite.sh` |
| SecCheck | [seccheck/README.md](seccheck/README.md) |
| Lite pen (owner lab) | [lab-pen/README.md](lab-pen/README.md) |

## Helper install sketch

1. Install Ubuntu to **SOLBOOT only** — **do not format** SOLLITE or SOLBRAIN.
2. Label volumes; add fstab (see full setup §8).
3. Install packages from full setup §9 (`modemmanager`, `network-manager`, `nmap`, …).
4. Autostart or bookmark Lite launcher against BRAIN paths; `SOL_LITE_REPO` → SOLLITE.
5. GRUB: “Studio SecCheck” / “Lab pen” → terminal cwd on BRAIN `sec/` + matching README.

## Ventoy alternative

Ventoy on BOOT; drop Helper live ISO + optional lab ISO. Persist state on BRAIN (and Lite on SOLLITE), not the live RAM disk.

## Mac / Apple Silicon

USB-boot **out of scope**. Use Carry-mode with host Python. See capability matrix in full setup.

## Verify (dated Pass — UNVERIFIED until hardware)

- [ ] Boots Helper Linux from stick (UEFI PC)
- [ ] SOLLITE + SOLBRAIN mount; Lite uses stick `data/`
- [ ] SecCheck refuses empty allowlist
- [ ] Lite-pen refuses without `I_OWN_THIS_LAB`
- [ ] Same `data/` visible in Windows/macOS Carry
