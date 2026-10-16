# Lenovo USB-C → 2.5G Ethernet

**What it is:** USB-C adapter presenting a 2.5 GbE RJ45 jack.

**Studio role:** Preferred **fast** wired NIC when the host has USB-C (stick enclosure laptop, modern Outpost). Same playbooks as ATHEN, higher link rate to switch/NAS/Pi (if Pi/switch support ≥1G).

## How to use

1. Plug into USB-C on the Helper/Carry host.
2. Cable to studio switch or target.
3. Check negotiated speed: `ethtool <iface>` (look for 2500Mb/s or 1000Mb/s).
4. Use for SecCheck / file sync / NAS when you want less flaky Wi‑Fi.

## Ubuntu Helper notes

- Packages: `network-manager`, `ethtool`.
- If the NIC is dead after plug-in, install firmware packages (`linux-firmware`) and reboot once.
- Chipset varies by Lenovo SKU; if Ubuntu does not see it, note the `lsusb` ID in your personal ops notes (do not commit secrets).

## Do not

- Assume 2.5G end-to-end if the switch or Pi is 1G-only (still fine at 1G).
- Replace allowlisting — speed ≠ permission.
