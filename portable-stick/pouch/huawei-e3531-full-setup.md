# Huawei E3531s-3 — full setup & configuration (OOB cellular)

**Role (historical):** Out-of-band **cellular uplink** for the stick laptop — **only where 3G/HSPA still exists**.  
**Not:** RF sniffer / Wi‑Fi monitor mode.  
**Short card:** [huawei-e3531.md](huawei-e3531.md)  
**Parent runbook:** [admin-toolbelt-full-setup.md](../../docs/user/admin-toolbelt-full-setup.md)

## Coverage reality (read first)

| Fact | Detail |
|------|--------|
| Radio | **2G/3G only** (HSPA+/UMTS). **No LTE/4G/5G.** Spec family: E3531s-1/2/3/6 — UMTS bands only. |
| **New Zealand** | Nationwide **3G shutdown complete** (carriers finished by ~Mar 2026). **This stick will not get mobile data on NZ networks.** |
| **Australia** | Major carriers already shut 3G — same outcome. |
| **Much of EU / UK** | 3G sunsets underway or done — assume **dead for live OOB** unless you verify a specific roaming/operator still offers 3G. |

**Studio implication:** Do **not** plan NZ/AU admin OOB on the E3531. Keep the guide for (a) residual use in rare regions that still run 3G, (b) USB/HiLink software practice offline, (c) replacement shopping. For live pouch OOB buy a **4G LTE or 5G** USB modem / MiFi instead.

Owner lab only. Use **your** SIM and **your** allowlisted targets — and only if the network still serves 3G.

---

## 0. What you need before starting

| Item | Notes |
|------|--------|
| E3531s-3 stick | USB-A (USB-C host → use A adapter) |
| Active SIM | Data plan; know PIN / PUK policy |
| Carrier **APN** | From carrier account portal or SIM pack — **do not put real APN/PIN in git** |
| Stick laptop | Prefer Ubuntu Helper on `SOLBOOT`; Windows/macOS Carry also works in HiLink mode |
| Packages (Ubuntu) | See §2 |

Write APN / Wi‑Fi / admin passwords on a **paper pouch card**, not in the repo.

---

## 1. Hardware prep

1. Power off / unplug the E3531.
2. Open the SIM tray; insert SIM (contact orientation per tray mark).
3. If the SIM has a PIN, have the PIN ready (three wrong tries → PUK).
4. Prefer a **direct USB port** on the laptop (avoid unpowered hubs).

---

## 2. Ubuntu Helper packages

```bash
sudo apt update
sudo apt install -y modemmanager network-manager usb-modeswitch usb-modeswitch-data \
  libqmi-utils ethtool iproute2 tcpdump
sudo systemctl enable --now ModemManager NetworkManager
```

Carry on Windows/macOS: use the stick’s **HiLink** web UI (§4) instead of ModemManager if that is easier.

---

## 3. Identify how the stick enumerates

Plug in, wait ~10 s, then:

```bash
lsusb | grep -i huawei
ip -br link
mmcli -L
```

### Common modes

| Mode | What you see | Good for |
|------|----------------|----------|
| **HiLink / CDC-Ether** | USB ethernet iface; often `192.168.8.1` web UI | Fast “just works” OOB internet |
| **Stick / modem** | `ttyUSB0`… and ModemManager entry | Cleaner NM mobile-broadband profile |
| **Mass storage only** | CD-ROM / install partition, no net | Need `usb-modeswitch` (§5) |

Record your `idVendor:idProduct` from `lsusb` (often starts as `12d1:1f01` then switches).

---

## 4. Path A — HiLink (recommended first)

Many E3531 units work as a tiny router over USB ethernet.

1. Plug in; wait for a new ethernet-like interface (`ip -br link`).
2. Browser: `http://192.168.8.1` (if that fails, try `http://192.168.1.1`).
3. Log in (default is often on a sticker / first-run wizard — **change it**).
4. Enter SIM PIN if prompted.
5. Mobile settings → set **APN** to your carrier’s value → save → connect.
6. Confirm host has a default route via the HiLink iface:

```bash
ip route
ping -c 3 1.1.1.1
```

7. Optional: disable **autodial** in the web UI only if you later switch to Stick/modem mode and see conflicts.

**Studio use:** SecCheck / lite-pen against **your** allowlisted hosts reachable over this uplink (cloud, DDNS Pi, etc.).

---

## 5. Path B — Stick / modem mode (ModemManager + NetworkManager)

Use when you want NM to own the WWAN profile, or HiLink is awkward.

### 5.1 Mode switch (if stuck on storage / wrong product ID)

IDs vary by firmware. After `lsusb`, if you still only see mass-storage:

```bash
sudo mkdir -p /etc/usb_modeswitch.d
```

Create a rule named for **your** current ID (example for common `12d1:1f01` → modem). Confirm MessageContent against a trusted guide for **your exact** `lsusb` IDs before relying on it:

```bash
# Example only — verify TargetProduct matches YOUR lsusb line
sudo tee /etc/usb_modeswitch.d/12d1:1f01 >/dev/null <<'EOF'
# Huawei E3531 — switch toward modem presentation (verify on your unit)
TargetVendor=0x12d1
TargetProductList="1001,1506,14dc,1f01"
MessageContent="55534243123456780000000000000011062000000100000000000000000000"
EOF
```

Unplug/replug (or reboot). Re-check:

```bash
lsusb | grep -i 12d1
dmesg | tail -n 40
ls /dev/ttyUSB* 2>/dev/null
mmcli -L
```

If mode-switch fails, fall back to **HiLink (§4)** — that is enough for OOB.

### 5.2 Connect with ModemManager / NetworkManager

```bash
mmcli -L
# Note modem index, e.g. 0
mmcli -m 0
```

Simple connect (replace APN; add user/password only if carrier requires):

```bash
# APN from YOUR carrier — example placeholder
sudo mmcli -m 0 --simple-connect='apn=YOUR_APN_HERE'
```

Persistent profile (preferred):

1. GUI: Settings → Network → Mobile Broadband → Add → pick modem → enter APN → Connect.  
2. Or CLI:

```bash
nmcli connection show
nmcli device
# Create interactive mobile connection (follow prompts):
nmcli connection add type gsm ifname '*' con-name sol-oob-cell apn YOUR_APN_HERE
nmcli connection up sol-oob-cell
```

Verify:

```bash
nmcli -t -f DEVICE,TYPE,STATE device
ip -br addr
ping -c 3 1.1.1.1
```

---

## 6. Windows / macOS Carry (HiLink)

1. Plug E3531; allow drivers if prompted.
2. Open `http://192.168.8.1` → APN + connect.
3. Confirm browser reaches the internet.
4. Run Lite Carry as usual; SecCheck uses this path when hosts are reachable.

---

## 7. Optional: capture **your** WWAN traffic only

Debug only — traffic you generate on this uplink:

```bash
# Find iface (HiLink ethernet or WWAN/ppp)
ip -br link
sudo tcpdump -i <iface> -n -c 50
```

Do **not** use this to monitor other people’s networks.

---

## 8. Studio playbooks

| Goal | Steps |
|------|--------|
| OOB admin / failover | **NZ: use 4G/5G modem** — not E3531. Legacy 3G regions only: E3531 up; studio Wi‑Fi off |
| External view of Pi | Same — needs a network that still serves this stick’s radio |
| Cell up + wire down | Legacy only; prefer Lenovo/ATHEN + modern cell modem |

---

## 9. Verify checklist

- [ ] `lsusb` shows Huawei after plug-in  
- [ ] HiLink UI **or** `mmcli -L` sees modem  
- [ ] APN set; data session up  
- [ ] `ping` / browser works without studio Wi‑Fi  
- [ ] SecCheck only against `hosts.allow`  
- [ ] Paper card has APN hint (no secrets in git)

---

## 10. Troubleshoot

| Symptom | Try |
|---------|-----|
| Only CD-ROM | `usb-modeswitch` + replug; or use Windows to let vendor switch once |
| HiLink UI blank | Try other USB port; wait longer; check `ip addr` for `192.168.8.x` |
| SIM locked | Enter PIN in UI / `mmcli`; avoid PUK lockout |
| No signal | Window/location; confirm plan active |
| Conflict HiLink + modem | Pick one path; disable autodial in HiLink if using Stick mode |
| Wrong APN | Carrier portal; temporary “internet” only if they document it |

## Do not

- Flash random “unlock” firmware as default ops.  
- Scan third-party nets.  
- Commit APN passwords, PINs, or `I_OWN_THIS_LAB` contents.
