# SOL-Lite host git repos (open in place + trusted remotes + PRs)

## Decision

Extend the existing `repository_*` tool surface so SOL-Lite can work on real host checkouts the way Cursor does: open the repo where it already lives, stage/commit locally, pull/merge/push on trusted paths, and create/merge hosting PRs via `gh`.

Do not introduce a host-git daemon. Do not rely on unrestricted terminal `git`/`gh` as the primary path. Keep workspace path containment and audit.

## Goals

1. Open an existing host git working tree in place as the session workspace (no clone into a SOL-Lite sandbox required).
2. Full local lifecycle: status, branch, checkout, stage, commit, pull, merge, push.
3. For trusted host roots: remotes and PR tools run without repeated `repository.remote` approvals.
4. GitHub PRs via host `gh` (create, status, merge). Local git remains usable when `gh` is missing.
5. On merge conflicts: agent may apply simple resolutions, then must get exact approval of the resolved tree before completing the merge and before push.

## Non-goals (this pass)

- Multi-root “Add Folder to Workspace”
- GitLab (or other host) adapters
- Force-push, hard reset of unrelated work, interactive rebase UI
- Embedded tokens or credential storage inside SOL-Lite (use host git credential helper / `gh` auth)

## Architecture

```text
/workspace <host-path>
        │
        ▼
WorkspaceManager.register (realpath)
        │
        ▼
Git root detect (rev-parse --show-toplevel)
        │  offer to register toplevel if user pointed at a subfolder
        ▼
ToolContext.workspace_root == repo root
        │
        ├── repository_* local tools (existing + pull/merge/conflict)
        │
        └── TrustGate ──► remotes + hosting_* PR tools
                 │
                 ├─ under config trusted_roots?
                 ├─ first-use confirm recorded?
                 └─ yes → skip repeated repository.remote prompts
```

### Components

| Piece | Responsibility |
|---|---|
| Workspace open-in-place | Register host path; prefer git toplevel; no copy |
| Trust gate | Allowlist + first confirm; gates remotes/PRs |
| Repository tools | Local + pull/merge/conflict continue; path containment |
| Hosting adapter | `gh`-backed PR create/status/merge; clear failure if unavailable |
| Approvals/audit | Tree-changing and PR merge still approved; all actions audited |

## Trust model

Layered (all required for always-on remotes):

1. Path is the active workspace root (or its git toplevel registered as workspace).
2. Realpath is equal to or under a configured `repository.trusted_roots` entry.
3. Operator has completed first-use confirmation for that workspace root; confirmation is stored under `data/state/trusted-repos.json` (not in `sol-lite.yaml`).

### Config

Add to `config/sol-lite.yaml`:

```yaml
repository:
  trusted_roots:
    - "E:/git"
```

Paths are compared after `realpath` / normalize (same rules as `WorkspaceManager.normalize_root`).

### Behaviour

| State | Local stage/commit | fetch/pull/push | hosting PR tools |
|---|---|---|---|
| Not a git root / outside workspace | Reject | Reject | Reject |
| Git workspace, not allowlisted | Allowed (current write approvals) | Denied; instruct how to add `trusted_roots` | Denied |
| Allowlisted, not first-confirmed | Allowed | Denied until one confirm | Denied until confirm |
| Allowlisted + confirmed | Allowed | Allowed without repeated remote approval | Allowed without repeated remote approval; PR merge still needs exact approval |

First confirm is prompted on the first remote or PR tool call for that root (interactive shell prompt or exact approval id, matching existing approval UX). There is no separate trust slash-command in this pass. Recording the confirm enables remotes for subsequent sessions on that root.

## Open in place

- `/workspace` and first-run already accept any host directory; this design makes that the primary path for host repos.
- If the user points at a subdirectory of a git work tree, detect toplevel and offer to register the toplevel instead so containment (`repo.relative_to(workspace)`) succeeds.
- `repository_clone_local` / `repository_clone_remote` remain for copying into a workspace; they are not required for day-to-day host work.

Containment rule stays: git toplevel must resolve inside the approved workspace root. For a host checkout, the workspace **is** that toplevel.

## Repository tools

### Keep

`repository_status`, `repository_diff`, `repository_log`, `repository_branches`, `repository_remotes`, `repository_create_branch`, `repository_checkout`, `repository_stage`, `repository_commit`, `repository_fetch`, `repository_push`, offline bundle/patch tools, clone tools.

### Add

| Tool | Behaviour |
|---|---|
| `repository_pull` | Fetch then integrate into current branch. Default: fast-forward only. Argument `strategy`: `ff-only` (default) or `merge` (creates a merge commit when needed; requires write approval). Always refuse a dirty worktree; operator must commit or stash outside this tool first. |
| `repository_merge` | Merge a named local or remote-tracking ref into the current branch (`git merge`). Refuse dirty worktree. On conflicts, stop mid-merge and return conflict paths. |
| `repository_conflict_status` | List conflicted paths and stage state; read-only. |
| `repository_resolve_and_continue` | After resolutions are in the tree, stage conflict paths and complete the in-progress merge (or equivalent). Requires exact approval that includes the resolved diff. |

### Agent surface

`sol_engineer` receives the new tools. Task-fit / allowlists updated so git-write and git-remote intents include pull, merge, conflict continue, and hosting PR tools.

## Conflict policy

1. Pull/merge that produces conflicts stops and returns the conflict file list. The repo may remain mid-merge.
2. The agent may apply **simple** resolutions only (e.g. whitespace-only, clearly marked ours/theirs when the operator intent is explicit, trivial both-added text). Ambiguous conflicts are left for explicit operator direction.
3. Before `repository_resolve_and_continue` completes the merge, show the resolved diff and require exact approval.
4. Before `repository_push` after a conflicted merge, the resolved commit must already exist; push follows trust rules above.
5. No silent force-push. No hard reset of unrelated work as part of conflict recovery.

## Hosting PRs (GitHub first)

Locked tool names:

| Tool | Behaviour |
|---|---|
| `hosting_pr_create` | Create PR via `gh` (base, head, title, body). Requires trust gate. |
| `hosting_pr_status` | Open/checks/mergeable summary via `gh`. Requires trust gate. |
| `hosting_pr_merge` | Merge PR (`method`: `merge` \| `squash` \| `rebase`) via `gh`. Requires trust gate **and** exact approval. |

Rules:

- Prefer host `gh` CLI; do not store PATs in SOL-Lite.
- If `gh` is missing or not authenticated, fail with a clear install/auth hint; local repository tools still work.
- Redact credentials from any logged URLs or stderr.
- GitLab and other hosts are out of scope for this pass; keep a thin adapter boundary so a later provider can plug in.

## Approvals and audit

- **Trusted remotes:** skip repeated `repository.remote` permission prompts once trust is satisfied.
- **Still require approval:** workspace writes outside role paths (existing), `repository_stage`, `repository_commit`, `repository_resolve_and_continue`, `hosting_pr_merge`, and any non-ff merge strategy that creates a merge commit when policy requires it.
- **Audit** every remote, merge, conflict-continue, trust confirm, and PR action with workspace root, trust state, refs, and approval id when used.

## Errors

Fail closed with plain messages:

- Repo outside workspace / not a git root
- Not allowlisted (how to add `trusted_roots`)
- Allowlisted but unconfirmed (prompt / deny until confirmed)
- Dirty tree when pull/merge refuses dirty
- Mid-merge conflict list without inventing a clean result
- `gh` missing / unauthenticated
- Network or auth failure from git/`gh` (stderr, credentials redacted)

## Testing

### Unit

- Trust root matching and normalize/realpath edge cases
- First-confirm state file read/write
- Pull/merge happy paths (mocked git)
- Conflict stop + resolve-continue approval gate
- Hosting tools with fake `gh` runner
- Untrusted remote denial

### Battle / security

- Open a temp host repo in place; stage and commit
- Trusted local remote mock for fetch/push
- Deny remotes for non-allowlisted workspace
- No path escape outside workspace
- PR merge path requires approval even when trusted

## Implementation notes

- Prefer extending `src/sol_lite/tools/repository.py`, permission scopes, registry remote sets, Engineer allowlists, and `docs/operations/repository-workflows.md`.
- Add a small trust helper (config + `data/state/trusted-repos.json`) used by remote and hosting tools.
- Update `config/sol-lite.yaml` with an empty or example `repository.trusted_roots` list and document it in getting-started / repository workflows.
- Keep offline bundle/patch workflows intact for air-gapped use.
