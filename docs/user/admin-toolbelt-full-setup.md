# Studio admin tool belt — full setup & configuration

Gapless runbook: blank ~500 GB M.2 → three partitions → Ubuntu Helper → SOL-Lite + encrypted brain → pouch network paths → SecCheck / Lab-pen.

**Who:** studio owner / admin only.  
**Day-1 short path:** [dummies-admin-stick-m2.md](dummies-admin-stick-m2.md)  
**Design:** [admin-toolbelt-full-setup-design](../superpowers/specs/2026-10-13-admin-toolbelt-full-setup-design.md)  
**Template tree:** [portable-stick/README.md](../../portable-stick/README.md)

---

## 1. Rules

1. Encrypt **SOLBRAIN**. Lost unencrypted brain = incident.
2. Never paste `owner_id`, tokens, or `I_OWN_THIS_LAB` into tickets/chat.
3. SecCheck / lite-pen only against hosts **you own** (`hosts.allow`). No third-party nets.
4. Stop Lite; safely eject before unplug.
5. Stick is **not** Outpost/Command SoT. Live hosts keep using `sol-git-upgrade` and host `data/`.
6. E3531 / R209 are **3G-only** gear — **not** RF sniffers. **NZ (and AU / much of EU) 3G is shut down:** E3531 is **dead for live OOB data**; R209 may still serve an **offline Wi‑Fi lab bubble** but not cellular WAN. Buy **4G/5G** replacements for real OOB.

---

## 2. Capability matrix (read this once)

| Host | Mount SOLLITE + SOLBRAIN | Run Lite (Carry) | USB-boot Helper / SecCheck / Lab-pen |
|------|--------------------------|------------------|--------------------------------------|
| UEFI PC (Windows or Linux firmware) | Yes | Yes | **Yes** — Ubuntu on `SOLBOOT` |
| Apple Silicon Mac (M1/M2/…) | Yes | Yes (host Python) | **No** — Apple cannot pure-USB-boot; Carry only ([Asahi FAQ](https://asahilinux.org/docs/project/faq/)) |
| Intel Mac | Yes | Yes | Treat as Carry (out of scope) |

“Any machine” for this belt means: **same brain + Lite everywhere you can mount volumes**; **boot personalities where UEFI USB boot works**.

---

## 3. Shopping list

| Item | Notes |
|------|--------|
| ~500 GB M.2 NVMe | Decent endurance |
| USB3/USB4 enclosure | USB-C **and** USB-A path |
| Optional cold-spare stick | Weekly BRAIN `data/` mirror |

### Pouch (physical — keep with the stick)

| Device | Doc |
|--------|-----|
| ATHEN USB→RJ45 female (LED) | [pouch/athen-usb-rj45-female.md](../../portable-stick/pouch/athen-usb-rj45-female.md) |
| Lenovo USB-C → 2.5G Ethernet | [pouch/lenovo-usbc-2.5g.md](../../portable-stick/pouch/lenovo-usbc-2.5g.md) |
| USB→RJ45 male | [pouch/usb-rj45-male.md](../../portable-stick/pouch/usb-rj45-male.md) |
| Short Cat6 (0.5–1 m) | Female NIC ↔ Pi / switch |
| Huawei E3531s-3 | Short [huawei-e3531.md](../../portable-stick/pouch/huawei-e3531.md) · **Full** [huawei-e3531-full-setup.md](../../portable-stick/pouch/huawei-e3531-full-setup.md) |
| R209-Z → **SOL-LAB-MIFI** | [vodafone-r209.md](../../portable-stick/pouch/vodafone-r209.md) · **[offline bubble](../../portable-stick/pouch/sol-lab-mifi-offline-bubble.md)** · **[soft-mod + AI](../../portable-stick/pouch/sol-lab-mifi-soft-modders.md)** |
| Optional monitor-mode Wi‑Fi USB | [pouch/optional-wifi-monitor.md](../../portable-stick/pouch/optional-wifi-monitor.md) |

### Host software (Carry)

| Software | When |
|----------|------|
| Python 3.11+ | Carry Lite |
| Git | Clone onto SOLLITE |
| Ollama (optional) | Local models or `SOL_OLLAMA_URL` |
| BitLocker / VeraCrypt / LUKS | Encrypt SOLBRAIN |
| balenaEtcher / Ubuntu ISO | Install Helper to SOLBOOT only |

---

## 4. Partition map (~500 GB)

| # | Label | FS | Size | Role |
|---|-------|-----|------|------|
| 1 | `SOLBOOT` | EFI + ext4 | ~96 GB | Ubuntu LTS Helper + GRUB (Helper / SecCheck / Lab-pen) |
| 2 | `SOLLITE` | **exFAT** | ~64 GB | Lite clone + venv — **no secrets** |
| 3 | `SOLBRAIN` | Encrypted (BitLocker / VeraCrypt / LUKS); inner exFAT/NTFS/ext4 | Rest (~320 GB+) | `data/`, `workspace/`, admin-belt, sec, reports; models ≤80 GB; leave ~20 GB free |

**Order tip:** Create all three unformatted/labelled first; install Ubuntu **only** to SOLBOOT; never format SOLLITE/SOLBRAIN during the Ubuntu installer.

---

## 5. Step-by-step — create volumes (HUMAN-OPS)

### Windows (Disk Management / `diskpart`)

1. Plug enclosure; open Disk Management.
2. Convert disk GPT if needed.
3. Create partitions with sizes above; assign labels `SOLBOOT`, `SOLLITE`, `SOLBRAIN` when formatting.
4. Format SOLLITE as **exFAT**.
5. Encrypt SOLBRAIN (BitLocker To Go recommended on Windows).
6. Leave SOLBOOT unformatted or ESP+ext4 from the Ubuntu installer (cleaner to let Ubuntu create EFI+root on that slice — shrink/create empty ~96 GB partition and install “Something else”).

### Linux (`gdisk` / `parted`)

1. Identify disk (`lsblk`) — **wrong disk = data loss**.
2. GPT: ~96 GB for boot, ~64 GB SOLLITE, rest SOLBRAIN.
3. `mkfs.exfat -n SOLLITE /dev/sdXN`
4. Encrypt SOLBRAIN (LUKS) then filesystem inside; or VeraCrypt container if you need Win+Mac unlock UX.
5. Label clearly: `SOLBOOT`, `SOLLITE`, `SOLBRAIN`.

**Carry-only first:** You may create only SOLLITE + SOLBRAIN, fill them, and add Ubuntu to SOLBOOT later.

---

## 6. Fill SOLLITE

1. Mount SOLLITE.
2. Follow [portable-stick/lite/README.md](../../portable-stick/lite/README.md).
3. Clone PLG_Ai_Lite to the volume root (or `sol-lite-src/`).
4. Create `.venv` and `pip install -e .` when online.

```powershell
# Windows example — adjust drive letter
cd E:\
git clone <your-lite-url> .
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

---

## 7. Fill SOLBRAIN

1. Unlock/mount SOLBRAIN.
2. Copy everything under repo `portable-stick/brain/` to the **root** of SOLBRAIN so you see:

```text
SOLBRAIN:\
  data\
  workspace\
  models\
  settings\
  launch\
  admin-belt\
  sec\
  studio-tools\
```

3. Copy examples to live files (do not commit secrets):

```powershell
cd X:\sec   # SOLBRAIN letter
copy hosts.allow.example hosts.allow
copy I_OWN_THIS_LAB.example I_OWN_THIS_LAB
# Edit hosts.allow — only your IPs/hostnames
# Edit I_OWN_THIS_LAB — set owner_id: <your id>
```

4. Optional: `settings\settings.yaml` from `settings.yaml.example`.
5. Models: only small GGUFs under `models/` (≤80 GB budget).

---

## 8. Install Ubuntu LTS on SOLBOOT

**Prefer:** Ubuntu **24.04 LTS** installed to SOLBOOT (not a live-only RAM disk). Ventoy + live ISO is alternate — still persist state on BRAIN.

1. Download Ubuntu Desktop/Server 24.04 ISO on another machine; write installer USB (or use Ventoy).
2. Boot installer on the **target PC** (not Apple Silicon).
3. **Something else** partitioning: install EFI + `/` **only** on the SOLBOOT slice. Do **not** format SOLLITE or SOLBRAIN.
4. After first boot, add fstab mounts for SOLLITE (exFAT) and SOLBRAIN (after unlock).

Example fstab ideas (adjust UUIDs):

```text
UUID=<sollite-uuid>  /mnt/SOLLITE   exfat  defaults,uid=1000,gid=1000,umask=0022  0 0
# SOLBRAIN: unlock LUKS/VeraCrypt/BitLocker then mount to /mnt/SOLBRAIN
```

5. GRUB menu entries (second/third): open a terminal cwd on `/mnt/SOLBRAIN/sec` and print [boot/seccheck](../../portable-stick/boot/seccheck/README.md) / [boot/lab-pen](../../portable-stick/boot/lab-pen/README.md) — or autostart Helper Lite launcher.

Detail: [portable-stick/boot/README.md](../../portable-stick/boot/README.md).

---

## 9. Ubuntu Helper packages

```bash
sudo apt update
sudo apt install -y \
  git python3 python3-venv curl rsync tmux openssh-client \
  udisks2 exfatprogs ntfs-3g \
  network-manager ethtool \
  modemmanager usb-modeswitch \
  nmap openssl dnsutils iproute2 tcpdump
# optional: libqmi-utils cryptsetup
```

| Bucket | Why |
|--------|-----|
| Base / venv | Lite + git |
| exfat / ntfs | SOLLITE + Win brains |
| NM + ethtool | ATHEN / Lenovo 2.5G / male NIC |
| ModemManager + usb-modeswitch | E3531 OOB |
| nmap / openssl / tcpdump | SecCheck support on **owned** nets only |

**Not default:** Kali metapackages, exploit frameworks, auto wide scans.

---

## 10. Network path playbooks

| Goal | Path |
|------|------|
| Pi on bench (direct) | Lenovo 2.5G **or** ATHEN female + Cat6 → Pi Ethernet; static IPs or link-local; SecCheck Pi IP |
| Studio LAN | Female NIC or male→switch; `hosts.allow` = studio hosts |
| External / OOB view | Needs **4G/5G** modem/MiFi in NZ — **not** E3531 (3G dead). Legacy: [E3531 full setup](../../portable-stick/pouch/huawei-e3531-full-setup.md) |
| Isolated lab bubble | **SOL-LAB-MIFI** (R209, no SIM) — [offline bubble](../../portable-stick/pouch/sol-lab-mifi-offline-bubble.md) · [soft-mod + AI](../../portable-stick/pouch/sol-lab-mifi-soft-modders.md) |
| Debug your traffic | `tcpdump` on **your** WWAN (4G/5G gear) or R209 LAN iface only |

Full device cards: [portable-stick/pouch/README.md](../../portable-stick/pouch/README.md).

---

## 11. SecCheck + Lab-pen

1. `hosts.allow` non-empty; only owned hosts.
2. `I_OWN_THIS_LAB` present with `owner_id:` for lite-pen / admin agent.
3. From BRAIN `sec/`:

```bash
python3 run_seccheck.py
# Lab-pen profile / ownership required:
python3 run_lite_pen.py
```

4. Reports → `workspace/sec-reports/` on SOLBRAIN.  
5. Docs: [sec/README.md](../../portable-stick/brain/sec/README.md).

---

## 12. Admin agent + daily Carry / Boot

### Carry (Windows / Linux / Mac)

1. Mount SOLLITE + unlock SOLBRAIN.
2. Run `SOLBRAIN/launch/Launch-SOL-Lite.ps1` or `.sh`.
3. Resolver sets `SOL_DATA_ROOT` / `SOL_WORKSPACE_ROOT` and discovers `SOL_LITE_REPO` on SOLLITE (or set env manually).
4. Switch agent to `sol_studio_admin` when unlocked ([admin-belt/07](../../portable-stick/brain/admin-belt/07-studio-admin-agent.md)). Builtin skill **`studio-admin-toolbelt`** loads for stick/pouch/SecCheck tasks.

### Boot Helper (UEFI PC)

1. Firmware boot from stick.
2. Unlock/mount BRAIN (+ SOLLITE).
3. `bash /mnt/SOLBRAIN/launch/Launch-SOL-Lite.sh`

### Mac (Apple Silicon)

Carry only: Python 3.11+, mount volumes, same launchers via bash if available or set env and `python -m sol_lite start`.

---

## 13. Verify checklist (hardware Pass = UNVERIFIED until you tick)

**Repo / no USB**

- [ ] `pytest tests/unit/test_portable_stick_root.py tests/unit/test_sec_allowlist.py -v`

**On stick**

- [ ] Three labels visible: SOLBOOT, SOLLITE, SOLBRAIN
- [ ] SOLBRAIN encrypted; SOLLITE has `pyproject.toml`
- [ ] Carry Lite starts; data lands on BRAIN
- [ ] Mac Carry works (if you use a Mac)
- [ ] UEFI PC boots Helper; mounts BRAIN
- [ ] SecCheck refuses empty allowlist
- [ ] Lite-pen refuses without ownership ack
- [ ] ATHEN or Lenovo gets link; E3531 connects WWAN; R209 bubble joins

---

## 14. Troubleshoot

| Symptom | Check |
|---------|--------|
| Lite starts but empty memory | Wrong `SOL_DATA_ROOT` — unlock BRAIN, re-run launcher |
| `SOL_LITE_REPO` missing | Mount SOLLITE; or `set SOL_LITE_REPO=...` / `SOL_LITE_VOLUME=` |
| E3531 only shows CD-ROM | `usb-modeswitch` / Stick mode |
| 2.5G stuck at 100M | Cable/switch; `ethtool` |
| Mac won’t boot Helper | Expected — Carry only |
| SecCheck no-op | Empty `hosts.allow` |
| Permission denied lite-pen | Missing `I_OWN_THIS_LAB` |

Safe eject: Stop Lite → unmount → OS “Safely remove”.

---

## 15. Doc index

| Doc | Role |
|-----|------|
| This file | Full setup |
| [dummies-admin-stick-m2.md](dummies-admin-stick-m2.md) | Day-1 short |
| [portable-stick/README.md](../../portable-stick/README.md) | Template overview |
| [pouch/README.md](../../portable-stick/pouch/README.md) | Hardware cards |
| [lite/README.md](../../portable-stick/lite/README.md) | SOLLITE fill |
| [admin-belt/README.md](../../portable-stick/brain/admin-belt/README.md) | Admin modules |
| [boot/README.md](../../portable-stick/boot/README.md) | Helper / GRUB |
