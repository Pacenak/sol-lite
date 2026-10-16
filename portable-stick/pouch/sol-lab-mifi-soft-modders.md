# SOL-LAB-MIFI — soft-modders guide (no brick) + AI assist

Maximize the R209-Z as **`SOL-LAB-MIFI`** using **stock web UI + host tools + SOL-Lite admin AI**.  
**Do not** flash OpenWrt, vendor “crack” firmware, or bootloader unlocks — high brick rate, low gain for an offline bubble.

**Primary bubble guide:** [sol-lab-mifi-offline-bubble.md](sol-lab-mifi-offline-bubble.md)

---

## Hard rules (stop here if tempted otherwise)

1. **Owned device only** — this R209, your Pi, your laptop.  
2. **No brick path** — no unsigned firmware, no SPI dumps “for fun,” no random unlock tools from forums.  
3. **No cracking foreign Wi‑Fi** — AI must not be asked to break other people’s WPA/WPS.  
4. **Skills ≠ permissions** — `sol_studio_admin` / `studio-admin-toolbelt` guide you; they do not unlock carrier magic or grant NETWORK abuse.  
5. Secrets stay on the **paper pouch card**, never in git or chat logs you paste into tickets.

---

## Tier 0 — Must do (already “max useful” for NZ)

| Soft mod | Where | Why |
|----------|--------|-----|
| Remove SIM | Hardware | Forces offline mindset; NZ 3G WAN is dead anyway |
| Rename SSID → `SOL-LAB-MIFI` | Wi‑Fi → Security | Studio identity |
| Strong WPA2 key | Same | Stops casual joins |
| Change web admin ≠ `admin` | Router settings | Stops casual UI takeover on the bubble |
| Disable WPS | Wi‑Fi / WPS page if present | Fewer foot-guns |
| Paper backup of factory + new creds | Pouch | Recover without reset |

After Tier 0 you are done for most SecCheck sessions.

---

## Tier 1 — Safe UI exploration (document what *your* unit has)

Walk the web UI once with a notebook. Tick what exists (firmware builds differ):

- [ ] Connected devices / DHCP client list  
- [ ] Wi‑Fi channel / bandwidth (20 MHz only is common)  
- [ ] SSID broadcast hide (optional; can make Pi join harder — usually leave visible)  
- [ ] MAC filter (optional allowlist of laptop + Pi MACs — easy to lock yourself out; set carefully)  
- [ ] Power save / battery display  
- [ ] USB mass-storage / charge-only behaviour when cabled to PC  
- [ ] SMS / Mobile Broadband pages (ignore for NZ WAN; leave alone)  
- [ ] Language / firmware version string (record version on paper)

**Method:** change **one** setting → Save → confirm laptop still joins → revert if bad. Never change five things at once.

### Channel pick (2.4 GHz only)

R209 is **not** 5 GHz and will not improve Lenovo **2.5 GbE**. For less interference at the bench:

```bash
# Ubuntu Helper — survey 2.4 GHz (your lab only)
nmcli device wifi list
# or: sudo iwlist wlan0 scan | less
```

Prefer channel **1, 6, or 11** with fewest strong neighbours. Set in UI if exposed; otherwise leave Auto.

---

## Tier 2 — Host-side “mods” (improve the *lab*, not the radio)

These make the bubble smarter without touching R209 firmware:

| Host mod | How |
|----------|-----|
| Static DHCP reservations | If UI lacks it: set **static IPs** on Pi + laptop inside `192.168.0.0/24` (e.g. Pi `.50`, laptop `.10`) — document on paper |
| `/etc/hosts` or mDNS | Map `pi-lab.sol` → Pi IP on the laptop for easier SecCheck names |
| `hosts.allow` on BRAIN | Always list Pi IP/hostname before SecCheck |
| Firewall reminder | On Pi, allow only what you are testing; bubble is not a security boundary by itself |
| Second path | Keep ATHEN/Lenovo Ethernet playbook for when Wi‑Fi is flaky |

---

## Tier 3 — AI-assisted config (SOL-Lite) — “make AI crack *your* setup”, not the device

Meaning of **AI assist** here: `sol_studio_admin` (unlocked) + skill **studio-admin-toolbelt** helps you **configure, verify, and troubleshoot** the bubble faster. It does **not** jailbreak the R209.

### Unlock

1. BRAIN `I_OWN_THIS_LAB` + feature flag (stick launcher).  
2. Start Lite → agent **SOL Studio Admin**.

### Prompts that are in-scope (copy/adapt)

```text
I own R209 SOL-LAB-MIFI offline bubble (no SIM). Gateway 192.168.0.1.
Help me: (1) checklist after rename to SOL-LAB-MIFI, (2) find Pi on 192.168.0.0/24,
(3) draft hosts.allow lines, (4) run studio_seccheck only on that Pi.
Do not suggest firmware flashes or attacking other SSIDs.
```

```text
From this nmcli wifi list output, recommend channel 1/6/11 for least conflict
at my bench. Stock R209 UI only — no OpenWrt.
```

```text
Pi joined SOL-LAB-MIFI but SecCheck fails. Walk unlock → hosts.allow →
studio_owner_status → studio_seccheck. Quote report path.
```

### Tools the admin agent should use

- `studio_owner_status`, `studio_seccheck`, `studio_lite_pen`  
- Workspace read/write for `hosts.allow` / notes on BRAIN  
- `execute_terminal_command` for `ip`, `nmcli`, `ping` (permission-gated)  
- Skill detail: `studio-admin-toolbelt` + this pouch guide

### Prompts that are **out of scope** (refuse / rewrite)

- Crack neighbour Wi‑Fi / WPS PIN attacks  
- “Flash this random firmware to unlock bands”  
- Dump NAND / glitch the bootloader  
- Use E3531/R209 as RF sniffer  

If the model suggests Tier‑brick items, stop and point it back at Tier 0–2.

---

## Explicitly rejected “max mods”

| Idea | Why reject |
|------|------------|
| OpenWrt / custom ROM | Brick-prone; R209-Z support sparse |
| Carrier unlock / band unlock tools | Irrelevant (no NZ 3G WAN); malware risk |
| Convert to 4G | Impossible — no LTE radio |
| Boost 2.5 G Ethernet / Wi‑Fi 6 | Different hardware; buy proper gear |
| Evil twin / captive portal kits | Out of studio policy |

---

## Factory reset (last resort — not a mod)

If you lock yourself out:

1. Use the hardware reset per R209 quickstart (often hold reset ~10 s — confirm on your unit’s card).  
2. Rejoins **factory** SSID/key from under the battery.  
3. Re-run [offline bubble §3](sol-lab-mifi-offline-bubble.md) (SOL-LAB-MIFI rename).

---

## Done when

- [ ] Tier 0 complete; paper card matches  
- [ ] Pi + laptop on `SOL-LAB-MIFI` without SIM  
- [ ] SecCheck/lite-pen report exists for **your** Pi  
- [ ] No firmware replaced; unit still boots stock UI  
- [ ] AI used only for checklist / allowlist / channel advice / tool runs  

**Replace later for real OOB internet:** 4G/5G MiFi. Keep R209 as the named offline bubble until it dies, then e‑waste recycle.
