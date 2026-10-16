# CHANGE CHECK — Portable Brain Stick (dual-mode)

Date: 2026-10-13

## WHAT CHANGED?

- Spec + plan for USB NVMe **BOOT (Linux) + BRAIN (Lite data/tools)** dual-mode
- In-repo `portable-stick/` template: launch/stop scripts, path resolver, studio-tools, boot HUMAN-OPS guide
- Unit tests for stick root / env resolution (no USB required)

## WHY?

Operator wants a personal helper that boots a mini OS when needed and, when the host OS is already running, mounts SOL-Lite + shared `data/` + portable studio tools.

## WHAT SYSTEMS ARE AFFECTED?

SOL-Lite docs and portable scaffolding only. No Outpost harness change. Uses existing `SOL_DATA_ROOT` / `SOL_WORKSPACE_ROOT`.

## WHAT APIs CHANGED?

None.

## WHAT DATA CHANGED?

Operator-owned stick `data/` / `workspace/` (not repo SoT).

## WHAT AGENTS ARE AFFECTED?

None in-studio; personal Lite on stick.

## WHAT SECURITY BOUNDARIES CHANGED?

Guidance: encrypt BRAIN; stop before unplug; no secrets in examples. Boot ISO install remains HUMAN-OPS.

## WHAT DOCUMENTATION MUST CHANGE?

- This CHANGE CHECK
- `portable-stick/README.md`, `boot/README.md`
- Spec/plan under `docs/superpowers/`
- Getting-started pointer

## WHAT TESTS MUST CHANGE?

- `tests/unit/test_portable_stick_root.py`

Live boot Pass: **UNVERIFIED** until dated on hardware.
