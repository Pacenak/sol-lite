# CHANGE CHECK — Admin tool belt full setup (3 partitions + pouch)

Date: 2026-10-13 · Repo: PLG_Ai_Lite

## WHAT CHANGED?

- Gapless full setup guide; dummies slimmed to day-1 pointer.
- Three-partition layout docs: `SOLBOOT` | `SOLLITE` | `SOLBRAIN`.
- Pouch hardware cards (ATHEN, Lenovo 2.5G, RJ45 male, E3531, R209, optional Wi‑Fi monitor).
- `resolve_stick_root` / launchers discover `SOL_LITE_REPO` on SOLLITE.
- Design + implementation plan committed under `docs/superpowers/`.

## WHY?

Operator needs one no-gap configure path, Mac Carry honesty, Ubuntu Helper packages, and studio-specific pouch roles (wired + cellular) without treating modems as sniffers.

## WHAT SYSTEMS ARE AFFECTED?

- `portable-stick/` template and docs only for runtime paths.
- Lite Carry launch env (`SOL_DATA_ROOT`, `SOL_WORKSPACE_ROOT`, `SOL_LITE_REPO`).
- No Outpost/Command product SoT change.

## WHAT APIs CHANGED?

None (HTTP). Env discovery only.

## WHAT DATA CHANGED?

None in databases. Operator volumes: Lite clone moves to SOLLITE by design; BRAIN keeps `data/`.

## WHAT AGENTS ARE AFFECTED?

`sol_studio_admin` unlock path unchanged (BRAIN sec files). Docs only.

## WHAT SECURITY BOUNDARIES CHANGED?

Documented: Mac no USB boot; cellular = OOB/MiFi not RF sniff; allowlist rules restated. No new attack tools.

## WHAT DOCUMENTATION MUST CHANGE?

Done: full setup, dummies, portable-stick README, boot, pouch, lite, admin-belt, getting-started pointer, this CHANGE CHECK.

## WHAT TESTS MUST CHANGE?

`tests/unit/test_portable_stick_root.py` — SOLLITE discovery + legacy brain clone.
