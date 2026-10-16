# Optional: monitor-mode USB Wi‑Fi

**What it is:** A separate USB Wi‑Fi adapter known to support **monitor mode** on Linux (common “Alfa-class” lab sticks). **Not** the E3531 or R209.

**Studio role (only if you buy one later):** authorized wireless checks on **SSIDs / APs you own** (studio lab, your Pi AP). Document chipset + Ubuntu package once you pick a model.

## Why separate

E3531 = cellular modem. R209 = carrier hotspot. Neither is a monitor-mode sniffer.

## Rules

- Owner lab only; no third-party networks.
- Do not commit driver blobs or exploit packs to this repo.
- Prefer documenting the exact `lsusb` ID in your private ops notes after purchase.
