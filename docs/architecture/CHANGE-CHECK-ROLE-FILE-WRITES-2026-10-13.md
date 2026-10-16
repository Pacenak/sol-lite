# CHANGE CHECK — Role-path file writes without click (2026-10-13)

**WHAT CHANGED?** `write_workspace_file` / `edit_workspace_file` under an agent's role roots run when `filesystem.write` is enabled. No `y`/`s` click. Outside-role paths still raise `ApprovalRequired`. Tool schemas no longer require `approval_id` / `plan` for the call to be valid. Agent prompts tell PA, Docs, Business, and Engineer to create plans and files instead of claiming no permission.

**WHY?** Agents refused ordinary asks like “make me a new plan” because every write waited on human approval, even inside role roots.

**WHAT SYSTEMS ARE AFFECTED?** Filesystem tools, role roots, approval UX for outside-role only, agent prompts.

**WHAT APIs CHANGED?** None (same tools; softer gate for in-role paths).

**WHAT DATA CHANGED?** None.

**WHAT AGENTS ARE AFFECTED?** `sol_pa`, `sol_docs`, `sol_business`, `sol_engineer`.

**WHAT SECURITY BOUNDARIES CHANGED?** In-role writes are capability-gated by `filesystem.write` enabled, not per-click approval. Outside-role, delete, move, terminal mutate, and destructive commands unchanged.

**WHAT DOCUMENTATION MUST CHANGE?** This file. `docs/user/approvals.md`, `docs/user/permissions.md`, `docs/architecture/permissions.md`.

**WHAT TESTS MUST CHANGE?** `tests/unit/test_session_approvals.py` (role write without approval; unbound still needs approval).
