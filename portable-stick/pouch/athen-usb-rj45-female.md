# ATHEN USB → RJ45 female (LED)

**What it is:** USB-A NIC dongle with an Ethernet jack and a link LED.

**Studio role:** Default wired path from stick laptop / Outpost workstation onto **your** studio LAN, or **direct cable to a Pi** (with a short Cat6 patch).

## How to use

1. Boot Helper OS (UEFI PC) or use Carry on the host OS.
2. Plug ATHEN into USB-A (use USB-C↔A if needed).
3. Patch cable: ATHEN jack → studio switch **or** Pi Ethernet.
4. Confirm link light; `nmcli device` / `ip link` shows the NIC.
5. Run SecCheck / lite-pen only against names in `hosts.allow`.

## Ubuntu Helper notes

- Needs `network-manager`, `ethtool`.
- Most Atheros/Realtek USB NICs work out of the box on Ubuntu 24.04.
- Prefer this over Wi‑Fi for stable SecCheck.

## Do not

- Bridge onto networks you are not authorized to test.
- Confuse with the **male** jack adapter (that plugs into a wall/switch port).
