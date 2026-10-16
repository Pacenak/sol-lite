# Portable Brain Stick Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an in-repo BRAIN stick template (launchers, layout, studio-tools, docs) so an operator can format a USB NVMe as Boot+Brain and run SOL-Lite carry-mode on Windows/Linux with shared `data/`.

**Architecture:** Template under `portable-stick/` with env-based Lite roots (`SOL_DATA_ROOT`, `SOL_WORKSPACE_ROOT`). Boot OS remains HUMAN-OPS documented, not vendored.

**Tech Stack:** PowerShell + POSIX sh launchers, Python path probes, Markdown ops guides.

## Global Constraints

- Do not vendor OS ISOs or secrets.
- Prefer existing Lite env vars; no second harness.
- Tests must not require physical USB hardware.

---

### Task 1: Scaffold BRAIN layout + launchers

**Files:**
- Create: `portable-stick/README.md`
- Create: `portable-stick/brain/.gitkeep` paths via README layout
- Create: `portable-stick/brain/launch/Launch-SOL-Lite.ps1`
- Create: `portable-stick/brain/launch/Launch-SOL-Lite.sh`
- Create: `portable-stick/brain/launch/Stop-SOL-Lite.ps1`
- Create: `portable-stick/brain/launch/Stop-SOL-Lite.sh`
- Create: `portable-stick/brain/launch/resolve_stick_root.py`
- Create: `tests/unit/test_portable_stick_root.py`

- [x] Resolve stick root from launcher path
- [x] Set SOL_DATA_ROOT / SOL_WORKSPACE_ROOT
- [x] Unit test path resolution

### Task 2: Extras — studio-tools + settings stub + boot ops

**Files:**
- Create: `portable-stick/brain/studio-tools/README.md`
- Create: `portable-stick/brain/studio-tools/gitea-project-git.md`
- Create: `portable-stick/brain/settings/settings.yaml.example`
- Create: `portable-stick/boot/README.md` (Linux/Ventoy HUMAN-OPS)
- Modify: `docs/getting-started/full-setup-first-run.md` (pointer)
- Create: `docs/architecture/CHANGE-CHECK-PORTABLE-BRAIN-STICK-2026-10-13.md`

- [x] Document partition + extras
- [x] Link from getting-started
