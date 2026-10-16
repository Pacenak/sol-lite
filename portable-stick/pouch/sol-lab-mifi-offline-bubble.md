# SOL-LAB-MIFI — offline lab bubble (R209-Z, no SIM)

Gapless guide: turn the Vodafone **R209-Z** into a named studio **offline Wi‑Fi bubble** for laptop + Pi SecCheck — **no cellular WAN required** (NZ 3G is dead anyway).

**Hardware:** R209-Z  
**SSID target name:** `SOL-LAB-MIFI`  
**Soft-mod / AI assist (no brick):** [sol-lab-mifi-soft-modders.md](sol-lab-mifi-soft-modders.md)  
**Legacy cellular notes:** [vodafone-r209-full-setup.md](vodafone-r209-full-setup.md)  
**Parent:** [admin-toolbelt-full-setup.md](../../docs/user/admin-toolbelt-full-setup.md)

## What this is / is not

| Is | Is not |
|----|--------|
| Battery 2.4 GHz AP + DHCP LAN (`192.168.0.x` typical) | 4G/5G internet (radio is 3G-only; NZ WAN dead) |
| Isolated path for **your** Pi + stick laptop | Evil twin / foreign Wi‑Fi attacks |
| Soft-config only (web UI) | OpenWrt flash / bootloader unlock (brick risk) |
| Works **without SIM** (you confirmed) | A way to “boost” Lenovo 2.5 GbE or modern Wi‑Fi |

---

## 0. Shopping / pouch card (paper only)

Write on paper (never git):

```text
SOL-LAB-MIFI
WPA2: ________________
Web UI admin: ________
Gateway: 192.168.0.1 (confirm)
Factory SSID/key (backup): ________ / ________
```

---

## 1. Prep

1. Charge R209 (USB).  
2. **Remove SIM** (or leave out) — offline bubble mode.  
3. Note factory SSID + WPA2 under battery / reminder card (recovery if you forget the new key).  
4. Stick laptop ready (Helper Ubuntu or Carry). Pi charged.

---

## 2. First join (factory SSID)

1. Power on R209; wait for Wi‑Fi LED ready.  
2. Laptop joins **factory** SSID + key from label.  
3. Confirm DHCP:

```bash
ip -br addr          # expect 192.168.0.x
ping -c 2 192.168.0.1
```

Windows: `ipconfig` → `192.168.0.x`. macOS: Wi‑Fi details → TCP/IP.

4. Browser → try in order:
   - `http://192.168.0.1`
   - `http://vodafonemobile.wifi`
   - `http://m.home`
5. Login: default web password is often `admin` — change in next step.

---

## 3. Harden + rename to SOL-LAB-MIFI

In web UI (menus vary slightly by firmware):

1. **Admin password** — Router → Router Settings (or Account) → set a strong password → Save.  
2. **Wi‑Fi** — Wi‑Fi → Security:
   - **SSID:** `SOL-LAB-MIFI`
   - **Key:** long random WPA2 (≥16 chars)
   - Save  
3. Laptop will drop — **rejoin** `SOL-LAB-MIFI` with the new key.  
4. Re-open web UI; confirm login with **new** admin password.  
5. **Disable WPS** if the UI offers it (reduces accidental joins).  
6. Optional: set a quiet **2.4 GHz channel** (1 / 6 / 11) if the UI exposes it — pick the least crowded at your bench (see soft-modders guide + AI assist).  
7. Update the **paper** pouch card.

Do **not** commit SSID/password/admin to the Lite repo.

---

## 4. Add the Pi (AI box)

1. On Pi: join `SOL-LAB-MIFI` + WPA2 key (GUI, `nmcli`, or raspi-config Wi‑Fi).  
2. Prefer staying on bubble only for the test (no studio Ethernet unless you intend dual-home).  
3. Find Pi IP:

```bash
# From laptop on SOL-LAB-MIFI
ip neigh
ping -c 2 <pi-hostname>.local   # if mDNS works
```

Or web UI → connected devices list.

4. On SOLBRAIN: add Pi to `sec/hosts.allow` (IP and/or hostname you will use).  
5. Unlock admin agent if needed; run SecCheck / lite-pen **only** against that allowlist.

---

## 5. Stick laptop + Lite

1. Mount SOLLITE + SOLBRAIN; launch Lite.  
2. Switch to `sol_studio_admin` when unlocked.  
3. Skill **studio-admin-toolbelt** / this guide for procedures.  
4. `studio_seccheck` / `studio_lite_pen` → quote `workspace/sec-reports/`.  
5. Optional debug on **your** bubble only:

```bash
ip -br link
sudo tcpdump -i wlan0 -n host <pi-ip>
```

---

## 6. Day-to-day ops

| Action | How |
|--------|-----|
| Start session | Power R209 → join SOL-LAB-MIFI → unlock BRAIN → Lite |
| End session | Stop Lite → forget nothing required → power off R209 → charge if low |
| No internet warning on phone | Normal — stay connected anyway |
| Studio Wi‑Fi “steals” clients | Forget studio SSID for the session or disable Wi‑Fi auto-join |

---

## 7. Verify checklist

- [ ] No SIM (or SIM ignored); AP still up  
- [ ] SSID is `SOL-LAB-MIFI`; factory key retired  
- [ ] Admin password ≠ `admin`  
- [ ] Laptop + Pi both `192.168.0.x` (or documented LAN)  
- [ ] Ping Pi works  
- [ ] Pi in `hosts.allow`  
- [ ] SecCheck/lite-pen report written  
- [ ] Paper pouch card matches live config  

---

## 8. Troubleshoot

| Symptom | Fix |
|---------|-----|
| No SSID | Charge; power cycle; factory reset only as last resort (restores factory SSID — re-do §3) |
| Joined but no `192.168.0.1` | Wrong Wi‑Fi; VPN off; static IP conflict — use DHCP |
| Pi won’t join | 2.4 GHz only; key typo; bring closer |
| “No internet” and OS drops Wi‑Fi | Set “stay connected” / disable auto-switch to cellular |
| Want real OOB internet | Buy **4G/5G MiFi** — do not expect NZ data from R209 |

---

## 9. Related

- Soft mods + **AI-assisted** config (no brick): [sol-lab-mifi-soft-modders.md](sol-lab-mifi-soft-modders.md)  
- Wired Pi path: [athen-usb-rj45-female.md](athen-usb-rj45-female.md) / [lenovo-usbc-2.5g.md](lenovo-usbc-2.5g.md)  
- Recycle E3531 (no NZ role): [huawei-e3531.md](huawei-e3531.md)
