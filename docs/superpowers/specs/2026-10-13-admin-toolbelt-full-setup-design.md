# Admin Tool Belt Full Setup — Design

> Status: APPROVED direction (operator: 2026-10-13)  
> Audience: Studio owner / admin only  
> Last updated: 2026-10-13  
> Related: [portable-brain-stick-design](2026-10-13-portable-brain-stick-design.md) (2-partition brain era — **superseded for admin belt by this 3-partition layout**), [studio-admin-toolbelt-stick plan](../plans/2026-10-13-studio-admin-toolbelt-stick.md)

## Intent

One ~500 GB USB3 NVMe **studio admin tool belt** that:

1. **Boots Ubuntu LTS Helper** (plus SecCheck / Lab-pen GRUB entries) on **UEFI PCs**.
2. **Carries** the same Lite + encrypted brain on **any host OS** that can mount the volumes (Windows, Linux, **macOS including Apple Silicon**) — run Lite and admin/sec runners on the host without USB-booting.
3. Documents **pouch hardware** (wired NICs + cellular) for owner-authorized studio / Pi lab paths only.
4. Ships a **gapless** full setup runbook in-repo (not tribal knowledge).

## Decisions locked (brainstorming)

| Decision | Choice |
|----------|--------|
| Guide location | New `docs/user/admin-toolbelt-full-setup.md`; dummies guide stays short starter + pointer |
| Apple Silicon / Mac | **Carry-only** — factual: Apple Silicon cannot pure-USB-boot Helper/SecCheck/Lab-pen (Asahi FAQ: no external-storage boot without internal boot pieces) |
| Helper OS | **Ubuntu LTS** (24.04 preferred; 22.04 OK) |
| Partitions | **Three:** `SOLBOOT` \| `SOLLITE` \| `SOLBRAIN` |
| Cellular roles | E3531 = OOB uplink; R209 = lab MiFi — **not** RF sniffers |
| Optional later | Separate USB Wi‑Fi with monitor mode for authorized wireless on **owned** SSIDs — not these two modems |
| Repo | PLG_Ai_Lite main tree (`portable-stick/` + `docs/`) |

## Non-goals

- MacBook USB-boot of Helper / SecCheck / Lab-pen.
- Shipping OS ISOs or Kali metapackages in git.
- Custom modem firmware / carrier unlock / evil-twin / third-party network attacks.
- Replacing Outpost/Command as studio SoT; stick is admin pouch + personal Lite brain.
- Using E3531/R209 as promiscuous RF sniffers (hardware unfit).

## Capability matrix

| Host | Mount SOLLITE + SOLBRAIN | Run Lite (Carry) | USB-boot Helper / SecCheck / Lab-pen |
|------|--------------------------|------------------|-------------------------------------|
| UEFI PC (Win/Linux firmware) | Yes | Yes | Yes (Ubuntu on `SOLBOOT`) |
| Apple Silicon Mac | Yes (exFAT LITE; unlock BRAIN) | Yes (host Python) | **No** — Carry only |
| Intel Mac | Same as Carry | Yes | Unreliable / out of scope; treat as Carry |

## Partition layout (~500 GB)

| Label | FS | Size | Role |
|-------|-----|------|------|
| `SOLBOOT` | EFI + ext4 | ~96 GB | Ubuntu LTS Helper + GRUB: Helper / SecCheck / Lab-pen. Replaceable. |
| `SOLLITE` | exFAT (Win/Mac/Linux) | ~64 GB | Lite git clone + venv; launchers may live here or stay on BRAIN with `SOL_LITE_REPO` → LITE. **No** secrets / `data/`. |
| `SOLBRAIN` | Encrypted (BitLocker / VeraCrypt / LUKS) | Rest (~320 GB+) | `data/`, `workspace/`, admin-belt, `sec/`, reports, models ≤80 GB, ~20 GB free reserve |

### Env / launcher contract

| Variable | Points to |
|----------|-----------|
| `SOL_LITE_REPO` | `SOLLITE` root (or `sol-lite-src/` on it) |
| `SOL_DATA_ROOT` | `SOLBRAIN/data` |
| `SOL_WORKSPACE_ROOT` | `SOLBRAIN/workspace` |
| `SOL_LITE_SETTINGS_FILE` | `SOLBRAIN/settings/settings.yaml` when present |
| Admin unlock | Existing `I_OWN_THIS_LAB` / `studio_owner.unlock` on BRAIN |

`resolve_stick_root` / launch scripts must learn **two** volume roots (LITE + BRAIN), not assume Lite lives only under BRAIN.

## Ubuntu Helper package set

| Bucket | Packages |
|--------|----------|
| Base | `git`, `python3`, `python3-venv`, `curl`, `rsync`, `tmux`, `openssh-client` |
| Disk | `udisks2`, `exfatprogs`, `ntfs-3g`, cryptsetup as needed |
| Wired | `network-manager`, `ethtool` (+ firmware notes for 2.5G) |
| Cellular (E3531) | `modemmanager`, `usb-modeswitch`, optional `libqmi-utils`, NM WWAN |
| Wi‑Fi (R209 client) | NetworkManager Wi‑Fi (stock) |
| Sec support | `nmap` (safe/allowlisted use), `openssl`, `dnsutils`, `iproute2`, `tcpdump` (owned nets only) |

Not default: Kali meta, exploit frameworks, auto wide scans.

## Pouch hardware (studio modification / config)

Physical tools; documented as cards under `portable-stick/pouch/`.

| Item | Studio role |
|------|-------------|
| **ATHEN** USB→RJ45 **female** (LED) | Primary USB-A NIC for studio LAN / direct cable to Pi |
| **Lenovo** USB-C → **2.5G** Ethernet | Preferred fast NIC when host has USB-C |
| USB→RJ45 **male** | Plug into wall jack / switch without a patch lead |
| Short Cat6 patch | Female NIC ↔ Pi or switch |
| **Huawei E3531s-3** | **OOB cellular uplink** for stick laptop; optional `tcpdump` on **your** WWAN only |
| **Vodafone R209-Z** | **Lab MiFi** bubble (laptop + Pi off studio LAN); optional capture on **that** LAN only |
| Optional later | Monitor-mode USB Wi‑Fi — authorized wireless on owned SSIDs (separate from E3531/R209) |

### Cellular — why not “sniffer”

- E3531 is a modem, not an RF sniffer; no Wi‑Fi monitor mode.
- R209 is a carrier hotspot AP; it does not provide monitor-mode sniffing of foreign Wi‑Fi.
- Best extra for sniffing **owned** lab traffic on those paths: `tcpdump`/`wireshark` on the laptop interface that carries **your** session — debug, not war-driving.
- Real RF/Wi‑Fi monitor work needs a different adapter.

## Deliverables (implementation)

1. **`docs/user/admin-toolbelt-full-setup.md`** — gapless TOC: rules → matrix → shop → 3-partition encrypt → SOLLITE → SOLBRAIN → Ubuntu BOOT → packages → network playbooks → SecCheck/Lab-pen → admin agent → verify → troubleshoot.
2. **`portable-stick/pouch/*.md`** — one card each: ATHEN, Lenovo 2.5G, RJ45 male, E3531, R209 (+ optional Wi‑Fi monitor stub).
3. **Updates:** `docs/user/dummies-admin-stick-m2.md` (pointer + day-1); `portable-stick/README.md`; `boot/README.md`; admin-belt index; budget tables → 3 labels.
4. **Code (minimal):** launchers / `resolve_stick_root` discover `SOLLITE` + `SOLBRAIN`; tests for path resolution.
5. **CHANGE CHECK** doc for this change set.
6. Hardware Pass checklists remain **UNVERIFIED** until operator runs them.

## Success criteria

- Operator can follow full setup with no missing steps from blank M.2 to Carry + Boot Helper.
- Mac user understands Carry-only and can run Lite + sec runners from host.
- Pouch cards name real devices and studio playbooks (Pi wired, OOB cell, MiFi bubble).
- SecCheck / lite-pen remain allowlist + ownership gated.
- Pytest for path/env helpers green without physical USB.

## Open for implementation plan only

- Exact GRUB menu text / Ventoy vs installed Ubuntu choice (document both; prefer installed Helper).
- Whether launchers physically move from BRAIN to SOLLITE or stay on BRAIN with `SOL_LITE_REPO` (prefer: keep launchers on BRAIN template copy for admin unlock locality; `SOL_LITE_REPO` → SOLLITE).
