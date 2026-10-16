# SecCheck + lite pen (studio owner)

**SecCheck** — defensive TCP/TLS smoke on allowlisted hosts.  
**Lite pen** — recon-only (banners / HTTP HEAD / TLS) on the same allowlist, plus `I_OWN_THIS_LAB`.

Neither tool ships exploits, brute force, or destructive checks.

## Setup on BRAIN

```text
cp hosts.allow.example hosts.allow          # edit with your studio IPs/hostnames
cp I_OWN_THIS_LAB.example I_OWN_THIS_LAB    # required for lite-pen only
```

## Run (carry or boot-mounted BRAIN)

```bash
cd /path/to/BRAIN/sec
python3 run_seccheck.py
python3 run_lite_pen.py
```

Reports: `../workspace/sec-reports/*.json`

## Rules

- Empty or missing allowlist → refuse
- Target not on allowlist → refuse
- Lite-pen without ack file / phrase → refuse
- Do not point at third-party networks
