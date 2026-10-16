# CHANGE CHECK — Studio Admin Tool Belt Stick

Date: 2026-10-13

## WHAT CHANGED?

- Plan: full studio admin tool belt on 500 GB M.2 (carry + boot Helper + SecCheck + lite pen)
- `portable-stick/brain/admin-belt/` module index
- `portable-stick/brain/sec/` allowlist-gated SecCheck + lite-pen (recon only)
- Boot profile READMEs for SecCheck and Lab pen
- 500 GB budget + README rewrite; unit tests for allowlist/ack gates
- Owner-only agent `sol_studio_admin` (`requires_studio_owner`) + tools `studio_owner_status` / `studio_seccheck` / `studio_lite_pen`; stick launcher sets `SOL_STUDIO_OWNER` / `SOL_STUDIO_OWNER_ID` from `I_OWN_THIS_LAB`

## WHY?

Studio owner needs one pouch: personal Lite brain, admin cheatsheets, and authorized lab security testing without treating the stick as product SoT.

## WHAT SYSTEMS ARE AFFECTED?

PLG_Ai_Lite `portable-stick/` docs and scripts only.

## WHAT APIs CHANGED?

None.

## WHAT DATA CHANGED?

Operator stick `hosts.allow`, `I_OWN_THIS_LAB`, `workspace/sec-reports/` (local).

## WHAT AGENTS ARE AFFECTED?

None in-studio.

## WHAT SECURITY BOUNDARIES CHANGED?

Allowlist + lab ack required for pen profile; no exploit payloads in repo; third-party targets refused by policy/docs.

## WHAT DOCUMENTATION MUST CHANGE?

- This CHANGE CHECK; portable-stick README; boot profiles; toolbelt plan

## WHAT TESTS MUST CHANGE?

- `tests/unit/test_sec_allowlist.py`

Live USB Pass: **UNVERIFIED**.
