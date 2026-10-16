# Boot profile: Lite pen (studio owner / authorized lab)

**You own the studio.** Still: allowlist + `I_OWN_THIS_LAB` required.

1. Prefer a **second GRUB entry** or **Ventoy ISO** labeled `LAB-PEN` so you do not land here by accident.
2. Mount BRAIN; copy ack + allowlist if missing.
3. `python3 run_lite_pen.py` from `BRAIN/sec`.
4. Optional on BOOT OS only (HUMAN-OPS): install `nmap` for manual follow-up **against allowlisted IPs you type yourself** — do not script blanket internet scans from this repo.

Recon-only scripts in-repo. No exploit payloads in git.
