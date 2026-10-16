# Admin Tool Belt Full Setup — Implementation Plan

> **For agentic workers:** Execute task-by-task in this session (operator requested implement). Spec: `docs/superpowers/specs/2026-10-13-admin-toolbelt-full-setup-design.md`.

**Goal:** Ship gapless full-setup docs, pouch hardware cards, 3-partition (`SOLBOOT`/`SOLLITE`/`SOLBRAIN`) launcher support, and repo pointers matching the approved design.

**Architecture:** Keep launchers + secrets on BRAIN; `SOL_LITE_REPO` points at SOLLITE (or legacy `brain/sol-lite-src`). Docs are the primary deliverable; code only teaches path discovery.

**Tech Stack:** Markdown runbooks, Python path resolver, pytest, bash/PowerShell launchers, Ubuntu LTS HUMAN-OPS.

## Global Constraints

- Apple Silicon = Carry-only (no USB Helper boot).
- Helper OS = Ubuntu LTS; no ISOs in git.
- SecCheck / lite-pen stay allowlist + ownership gated.
- E3531 = OOB cell; R209 = lab MiFi; not RF sniffers.
- Do not invent Outpost/Command behavior.

## File map

| Path | Role |
|------|------|
| `docs/user/admin-toolbelt-full-setup.md` | Gapless master runbook |
| `docs/user/dummies-admin-stick-m2.md` | Short day-1 + pointer |
| `portable-stick/pouch/*.md` | Hardware cards |
| `portable-stick/lite/README.md` | SOLLITE volume template |
| `portable-stick/README.md`, `boot/README.md`, `brain/admin-belt/README.md` | 3-partition + pouch links |
| `portable-stick/brain/launch/resolve_stick_root.py` + launchers | Discover SOLLITE |
| `tests/unit/test_portable_stick_root.py` | Path tests |
| `docs/architecture/CHANGE-CHECK-ADMIN-TOOLBELT-FULL-SETUP-2026-10-13.md` | CHANGE CHECK |
| `docs/getting-started/full-setup-first-run.md` | Pointer |

## Route

### Task 1: Resolver + tests (SOLLITE)

**Files:** `resolve_stick_root.py`, `test_portable_stick_root.py`, launch `.sh` / `.ps1`

- [ ] Add `find_lite_repo(brain)` — env `SOL_LITE_REPO`, legacy `brain/sol-lite-src`, sibling/`SOLLITE` mounts with `pyproject.toml`
- [ ] `env_for_brain` sets `SOL_LITE_REPO` when found
- [ ] Launchers prefer that env; still fall back to `brain/sol-lite-src`
- [ ] Pytest covers found / missing / legacy
- [ ] `pytest tests/unit/test_portable_stick_root.py -v` green

### Task 2: Pouch cards + lite template

**Files:** `portable-stick/pouch/{README,athen-usb-rj45-female,lenovo-usbc-2.5g,usb-rj45-male,huawei-e3531,vodafone-r209,optional-wifi-monitor}.md`, `portable-stick/lite/README.md`

- [ ] One card per device: role, connect steps, Ubuntu notes, don’ts
- [ ] Lite volume: clone layout, no secrets

### Task 3: Full setup runbook + dummies slim

**Files:** `docs/user/admin-toolbelt-full-setup.md`, rewrite `dummies-admin-stick-m2.md`

- [ ] Full TOC per spec § deliverables
- [ ] Dummies = day-1 only + link to full setup

### Task 4: Align portable-stick + getting-started + CHANGE CHECK

**Files:** README, boot README, admin-belt index, getting-started, CHANGE CHECK, toolbelt plan pointer

- [ ] All budgets say 3 partitions
- [ ] CHANGE CHECK answers WHAT/WHY/systems/docs/tests

### Task 5: Verify

- [ ] Pytest portable stick + sec allowlist still pass
- [ ] List new guides in commit message / reply to operator

## Decisions

- Launchers stay on BRAIN; `SOL_LITE_REPO` → SOLLITE.
- Installed Ubuntu Helper preferred; Ventoy documented as alternate.
- Interface repo: no stick docs today — no Interface change unless a Lite pointer is required (none).

## Done when

- Full setup + pouch cards exist; dummies points at them; resolvers/tests green; CHANGE CHECK committed with docs.
