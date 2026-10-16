# Boot profile: SecCheck (defensive)

1. Boot Helper Linux (or live ISO) with BRAIN mounted.
2. `cd /media/$USER/SOLBRAIN/sec` (adjust mount).
3. Ensure `hosts.allow` exists (from example).
4. `python3 run_seccheck.py`
5. Read `../workspace/sec-reports/seccheck-*.json`

No exploits. Allowlist only.
