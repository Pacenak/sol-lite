# Host Git Repos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Open host git checkouts in place, trust allowlist + first confirm for remotes, add pull/merge/conflict tools and GitHub PR tools via `gh`, so first-run local engineering works like Cursor.

**Architecture:** Extend `repository_*` tools; add `RepositoryTrust` (config roots + `data/state/trusted-repos.json`); enable `repository.remote` in policy; skip repeated remote approval when trusted; add `hosting_pr_*` via `gh`; detect git toplevel on workspace open and offer trust.

**Tech Stack:** Python 3.11+, existing ToolContext/PermissionEngine, git CLI, optional `gh` CLI.

## Global Constraints

- Keep workspace path containment (`repo` must be under workspace root).
- No embedded git credentials; use host helpers / `gh` auth.
- No force-push; no hard reset of unrelated work.
- Trust requires allowlist + first confirm; first-run UX may allowlist+confirm the exact opened repo root in one prompt.
- Spec: `docs/superpowers/specs/2026-10-13-host-git-repos-design.md`.

## File map

| File | Role |
|---|---|
| `src/sol_lite/repository/__init__.py` | Package export |
| `src/sol_lite/repository/trust.py` | Allowlist + confirm store |
| `src/sol_lite/tools/repository.py` | Pull/merge/conflict + trust-aware remote approval |
| `src/sol_lite/tools/hosting.py` | `hosting_pr_create/status/merge` via `gh` |
| `src/sol_lite/tools/base.py` | `repository_trust` on ToolContext |
| `src/sol_lite/tools/__init__.py` | Register hosting tools |
| `src/sol_lite/tools/registry.py` | Remote/mutating tool sets |
| `src/sol_lite/bootstrap.py` | Wire trust from config + state |
| `src/sol_lite/agents/shell.py` | Git toplevel + trust prompt on open |
| `src/sol_lite/agents/engineer/tools.yaml` | Expose new tools |
| `src/sol_lite/agents/task_fit.py` | Git tool name sets |
| `config/sol-lite.yaml` | `repository.trusted_roots` |
| `config/permissions.yaml` | Enable `repository.remote` |
| `docs/operations/repository-workflows.md` | Operator workflow |
| `docs/getting-started/full-setup-first-run.md` | First-run host repo steps |
| `tests/unit/test_repository_trust.py` | Trust unit tests |
| `tests/unit/test_repository_pull_merge.py` | Pull/merge/conflict tests |
| `tests/unit/test_hosting_pr.py` | Hosting adapter tests |
| `tests/unit/test_registry.py` | Manifest update |

---

### Task 1: Repository trust helper

**Files:**
- Create: `src/sol_lite/repository/__init__.py`
- Create: `src/sol_lite/repository/trust.py`
- Create: `tests/unit/test_repository_trust.py`
- Modify: `config/sol-lite.yaml`
- Modify: `config/permissions.yaml`

**Interfaces:**
- Produces: `RepositoryTrust(config_roots, state_path)`, methods `normalize(path)`, `is_allowlisted(root)`, `is_confirmed(root)`, `is_trusted(root)`, `confirm(root, *, allowlist_exact=False)`, `explain_denial(root) -> str`

- [ ] Implement trust module + unit tests; enable `repository.remote`; add empty `repository.trusted_roots` to yaml
- [ ] Run: `python -m pytest tests/unit/test_repository_trust.py -v`

### Task 2: Wire trust into ToolContext + bootstrap + open-in-place

**Files:**
- Modify: `src/sol_lite/tools/base.py`
- Modify: `src/sol_lite/bootstrap.py`
- Modify: `src/sol_lite/agents/shell.py`

- [ ] Add `repository_trust` to ToolContext/`for_workspace`
- [ ] Construct `RepositoryTrust` in bootstrap from `application["repository"]["trusted_roots"]` and `data/state/trusted-repos.json`
- [ ] On workspace register: if git subfolder, offer toplevel; if git root not trusted, offer allowlist+confirm for first-run

### Task 3: Pull, merge, conflict tools + trust-aware remotes

**Files:**
- Modify: `src/sol_lite/tools/repository.py`
- Modify: `src/sol_lite/tools/registry.py`
- Modify: `src/sol_lite/agents/task_fit.py`
- Modify: `src/sol_lite/agents/engineer/tools.yaml`
- Create: `tests/unit/test_repository_pull_merge.py`

- [ ] Add `_require_remote` that skips approval when `is_trusted`
- [ ] Add `repository_pull`, `repository_merge`, `repository_conflict_status`, `repository_resolve_and_continue`
- [ ] Update registry/task_fit/engineer tools; tests with real temp git repos

### Task 4: Hosting PR tools

**Files:**
- Create: `src/sol_lite/tools/hosting.py`
- Modify: `src/sol_lite/tools/__init__.py`
- Modify: `tests/unit/test_registry.py`
- Create: `tests/unit/test_hosting_pr.py`

- [ ] Implement `hosting_pr_create`, `hosting_pr_status`, `hosting_pr_merge` via `gh`
- [ ] Require trust; merge needs exact approval; fake `gh` in tests

### Task 5: Docs + first-run verification

**Files:**
- Modify: `docs/operations/repository-workflows.md`
- Modify: `docs/getting-started/full-setup-first-run.md`

- [ ] Document open-in-place, trust prompt, pull/merge/PR
- [ ] Run unit tests for registry + repository + trust + hosting
