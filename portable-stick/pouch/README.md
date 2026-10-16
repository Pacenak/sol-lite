# Admin pouch — physical tools

These are **hardware** you carry with the M.2 stick. They are not apps on BRAIN.

| Card | Device | Studio role |
|------|--------|-------------|
| [athen-usb-rj45-female.md](athen-usb-rj45-female.md) | ATHEN USB→RJ45 female (LED) | Wired NIC → studio LAN or Pi |
| [lenovo-usbc-2.5g.md](lenovo-usbc-2.5g.md) | Lenovo USB-C → 2.5G Ethernet | Fast NIC when host has USB-C |
| [usb-rj45-male.md](usb-rj45-male.md) | USB→RJ45 male | Wall jack / switch without patch lead |
| [huawei-e3531.md](huawei-e3531.md) | Huawei E3531s-3 (**3G only**) | **NZ/AU live OOB: dead** after 3G sunset — replace with 4G/5G modem. Legacy setup: **[full](huawei-e3531-full-setup.md)** |
| [vodafone-r209.md](vodafone-r209.md) | R209-Z → **SOL-LAB-MIFI** | Offline Wi‑Fi bubble (no SIM). **[bubble](sol-lab-mifi-offline-bubble.md)** · **[soft-mod + AI](sol-lab-mifi-soft-modders.md)** |
| [optional-wifi-monitor.md](optional-wifi-monitor.md) | Monitor-mode USB Wi‑Fi (optional) | Authorized wireless on **owned** SSIDs |

**Rules:** only networks and hosts you own; SecCheck / lite-pen use `hosts.allow` + ownership ack. Full playbooks: [admin-toolbelt-full-setup.md](../../docs/user/admin-toolbelt-full-setup.md).
