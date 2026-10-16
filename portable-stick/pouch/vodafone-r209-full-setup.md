# Vodafone Mobile WiFi R209-Z — full setup & configuration (lab MiFi)

**Role:** Portable **lab Wi‑Fi bubble** — stick laptop + Pi (+ phone) on one SSID that is **not** the studio LAN.  
**Not:** Wi‑Fi monitor-mode sniffer / evil twin.  
**Short card:** [vodafone-r209.md](vodafone-r209.md)  
**Preferred NZ use (no SIM):** [sol-lab-mifi-offline-bubble.md](sol-lab-mifi-offline-bubble.md) · [sol-lab-mifi-soft-modders.md](sol-lab-mifi-soft-modders.md)  
**Parent runbook:** [admin-toolbelt-full-setup.md](../../docs/user/admin-toolbelt-full-setup.md)

## Coverage reality (read first)

| Fact | Detail |
|------|--------|
| Radio | **3G / DC-HSPA+ only** (datasheet: LTE = N/A). GSM + UMTS 900/1900/2100 — **no 4G/5G.** |
| **New Zealand** | Nationwide **3G shutdown complete** (~Mar 2026). **No mobile WAN** on NZ SIMs through this MiFi. |
| **Australia / much of EU** | Same class of problem — 3G gone or going. |

**What still works without 3G WAN**

- R209 can often still broadcast its **Wi‑Fi AP** so laptop + Pi get a private `192.168.0.x` LAN **with no internet** — useful for isolated SecCheck/lite-pen of **your** Pi.
- It is **not** a substitute for OOB internet. For travel/OOB cellular, replace with a **4G/5G MiFi**.

Owner lab only. Use **your** devices on the bubble.

---

## 0. What you need before starting

| Item | Notes |
|------|--------|
| R209-Z unit + battery | Charge before first long session |
| Active SIM | Usually Vodafone (or compatible per device lock) |
| Label / reminder card | Factory **SSID** + **WPA2 key** are under the battery / on the card |
| Stick laptop | Helper Ubuntu or Carry (Win/Mac) |
| Pi (optional) | Wi‑Fi client for AI box under test |
| Paper pouch note | New SSID/admin password after you change defaults — **not in git** |

Official-style web UI hosts (try in order after you join Wi‑Fi):

- `http://192.168.0.1`
- `http://vodafonemobile.wifi`
- Sometimes `http://m.home`

Default **web admin** password on retail units is commonly `admin` — **change it** on first config.

---

## 1. Hardware prep

1. Power off R209.
2. Remove back cover / battery; insert SIM (tray orientation as marked).
3. Note factory SSID + Wi‑Fi key from the label **before** you close the cover.
4. Reassemble; charge via USB if battery is low.
5. Power on; wait until status LEDs show ready (see device quickstart if unsure).

---

## 2. First connect (any OS)

1. On the stick laptop (or phone): open Wi‑Fi list.
2. Join the factory **SSID**; enter the **WPA2 key** from the label.
3. Confirm DHCP: client should get an address like `192.168.0.x`.

```bash
# Ubuntu Helper after join
ip -br addr
ip route
ping -c 2 192.168.0.1
```

Windows: `ipconfig` — look for `192.168.0.x`.  
macOS: System Settings → Wi‑Fi → Details → TCP/IP.

4. Open a browser to `http://192.168.0.1` or `http://vodafonemobile.wifi`.
5. Log in with password `admin` (unless your unit’s card says otherwise).

---

## 3. Hardening & studio naming (do this once)

Still in the web UI:

1. **Change admin password**  
   Typical path: Router → Router Settings → admin password → Save.
2. **Rename Wi‑Fi SSID** to something studio-local, e.g. `SOL-LAB-MIFI` (not your home name).  
   Path: Wi‑Fi → Security → SSID + Key → Save.
3. Use a **strong WPA2 key**; write both SSID and key on the paper pouch card.
4. Rejoin the laptop on the **new** SSID.
5. Optional: disable WPS if you do not need it (reduces accidental joins).

Do not commit SSID/password to the Lite repo.

---

## 4. Mobile data / APN

R209 is often preconfigured for Vodafone. If data does not come up:

1. Web UI → **Mobile Broadband** / Network (labels vary by firmware).
2. Enter SIM **PIN** if asked (avoid lockout → PUK).
3. If APN is editable: set **your** carrier APN from the carrier portal (keep off tickets/git).
4. Network selection: Automatic unless you have a documented reason to lock a band/operator.
5. Confirm UI shows connected / has WAN; from a client:

```bash
ping -c 3 1.1.1.1
```

If clients get `192.168.0.x` but no internet: SIM plan, signal, or APN — not Lite.

---

## 5. Build the lab bubble (laptop + Pi)

### 5.1 Laptop (Helper or Carry)

1. Join `SOL-LAB-MIFI` (or your renamed SSID).
2. Prefer leaving **studio Ethernet disconnected** so SecCheck traffic stays on the bubble (or use policy routing if you know what you are doing).
3. Note laptop IP: `ip -br addr` / `ipconfig`.

### 5.2 Raspberry Pi (AI box)

1. On the Pi (monitor/SSH on another net, or first boot HDMI): join the same SSID + key.  
   Raspberry Pi OS: GUI Wi‑Fi or `nmcli` / `wpa_supplicant` as you already use for that image.
2. Reboot Pi on the bubble; find its IP:

```bash
# From laptop on R209 Wi‑Fi — only scan YOUR bubble if you must
ip neigh
# or check R209 web UI “connected devices”
```

3. Add the Pi hostname/IP to BRAIN `sec/hosts.allow`.
4. From stick laptop:

```bash
ping -c 3 <pi-ip>
# Then Lite sol_studio_admin → studio_seccheck / studio_lite_pen
```

### 5.3 Optional: phone UI

Join the same SSID to open Pi web UIs while testing.

---

## 6. Ubuntu Helper extras

```bash
sudo apt install -y network-manager iw wireless-tools tcpdump
nmcli device wifi list
nmcli device wifi connect 'YOUR_SSID' password 'YOUR_KEY'
```

Prefer 2.4 GHz if the Pi is fussy; R209 is typically single-band class hardware — use what the UI offers.

---

## 7. Optional: capture **your** bubble LAN only

On the laptop, while joined to R209:

```bash
ip -br link   # note the wlan iface
sudo tcpdump -i wlan0 -n host <pi-ip>
```

Only for debugging **your** Pi/services. Not for other people’s SSIDs.

---

## 8. Studio playbooks

| Goal | Steps |
|------|--------|
| Isolated Pi pen / SecCheck | R209 on (WAN optional/dead in NZ); laptop + Pi on SSID; `hosts.allow` = Pi; SecCheck/lite-pen |
| Travel lab with internet | **Replace with 4G/5G MiFi** — R209 has no NZ WAN |
| vs E3531 | Both 3G-dead in NZ; R209 may still do offline Wi‑Fi LAN; E3531 has no useful NZ role ([e3531](huawei-e3531-full-setup.md)) |

---

## 9. Verify checklist

- [ ] SIM seated; R209 powers on; LEDs healthy  
- [ ] Joined Wi‑Fi; got `192.168.0.x`  
- [ ] Web UI opens; admin password changed  
- [ ] SSID/key renamed and written on pouch paper  
- [ ] Mobile data works (if required for the test)  
- [ ] Pi + laptop on same SSID; Pi in `hosts.allow`  
- [ ] SecCheck/lite-pen run with report under `workspace/sec-reports/`

---

## 10. Troubleshoot

| Symptom | Try |
|---------|-----|
| No SSID in list | Charge battery; power cycle; reset only if documented (hold reset ~10 s — will wipe your SSID changes) |
| Can join but no web UI | Confirm `192.168.0.1`; try `vodafonemobile.wifi`; disable VPN on client |
| Forgot admin password | Factory reset per Vodafone/ZTE card; re-do §3 |
| Pi won’t join | Typo in key; 2.4 GHz only; power Pi closer; check country Wi‑Fi reg |
| Data down, Wi‑Fi up | APN / SIM PIN / signal / plan |
| Studio LAN “leaks” into test | Disconnect ethernet; forget studio Wi‑Fi for the session |

## Do not

- Evil-twin / captive-portal attacks.  
- Probe other people’s hotspots.  
- Treat R209 as a monitor-mode sniffer — see [optional-wifi-monitor.md](optional-wifi-monitor.md).  
- Commit SSID, Wi‑Fi key, admin password, or SIM PIN to git.
