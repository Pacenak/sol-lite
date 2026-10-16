# Repository Workflows

SOL-Lite works on a Git repository that already lives on the host machine. Open that
checkout as the workspace. Remote synchronization uses host Git credentials and, when
installed, the GitHub CLI (`gh`). Untrusted workspaces keep remotes blocked until you
allowlist and confirm them.

## Open a host repo (first run)

1. Start SOL-Lite and choose the real checkout path (for example `E:\git\plg-sol\MyRepo`).
2. If you pointed at a subdirectory, accept the offer to open the Git repository root.
3. When asked to trust remotes for that repo, answer `y` for Cursor-like pull/push/PR.
4. Optional: add parent paths under `repository.trusted_roots` in `config/sol-lite.yaml`
   so every repo under that tree is allowlisted; each workspace still needs one confirm
   (or the first-run trust prompt with `allowlist_exact` for that exact root).

Trust state is stored in `data/state/trusted-repos.json`. Local stage/commit still work
without trust; only remotes and hosting PR tools require it.

## Local engineering cycle

1. `repository_status` — establish repository root, branch, HEAD, upstream and working-tree state.
2. `repository_branches` / `repository_log` — establish available local history.
3. `repository_create_branch` — create an isolated work branch after approval.
4. Workspace write tools — edit the actual files after approval.
5. Validation — run the repository's real tests, lint, build and reproduction commands.
6. `repository_diff` — inspect the resulting change.
7. `repository_stage` — stage only the intended paths after approval.
8. `repository_diff(staged=true)` — inspect the staged change.
9. `repository_commit` — commit with an approved message.
10. `repository_status` — prove the resulting repository state.

## Pull, merge, and push

On a trusted workspace:

1. `repository_pull` — fetch and integrate (`ff-only` by default; `strategy=merge` needs write approval).
2. `repository_merge` — merge a named local or remote-tracking ref.
3. On conflicts: `repository_conflict_status`, edit/resolve simply, then
   `repository_resolve_and_continue` with exact approval of the resolved tree.
4. `repository_push` — push the branch (no repeated remote approval when trusted).

Dirty worktrees refuse pull/merge. Force-push is not offered.

## GitHub pull requests

Requires trusted remotes and `gh` on PATH (`gh auth login`).

1. `hosting_pr_create` — open a PR (base/head/title/body).
2. `hosting_pr_status` — number, checks, mergeable summary.
3. `hosting_pr_merge` — merge/squash/rebase after exact approval.

If `gh` is missing or unauthenticated, PR tools fail clearly; local Git tools still work.

## Offline transport

### Committed work

Use `repository_create_bundle`. The bundle is verified immediately after creation. Transfer the
`.bundle` file to the destination machine by an external mechanism.

On the destination machine:

1. Place the bundle inside the approved workspace.
2. Run `repository_import_bundle` with the source branch name.
3. Review the imported `refs/remotes/sol-offline/<branch>` ref.
4. Checkout the intended local branch if necessary.
5. Run `repository_merge_import` only when the current branch is clean and exactly matches the
   imported branch name. The merge is `--ff-only`; it cannot silently create a merge commit or
   resolve conflicts by discarding work.
6. Re-run validation.

### Uncommitted work

Use `repository_create_patch` to export the working-tree diff or staged diff. Transfer the patch
file separately. The destination uses `repository_apply_patch`, which first runs `git apply --check`
and then applies with `--index` so the result is immediately reviewable as a staged change.

Patches do not preserve arbitrary repository metadata or commit history. Use a bundle when the work
has been committed and Git history must be transported.

## Working with a fork

A fork is normally a server-side repository created by a hosting provider. SOL-Lite does not label a
local branch as a fork.

If the fork already exists, the agent can:

- clone it with `repository_clone_remote` when remotes are trusted or approved;
- inspect and edit it locally;
- set or update its remote with `repository_set_remote`;
- fetch changes with `repository_fetch`; and
- push an approved branch with `repository_push`.

If the machine is offline, remote operations cannot occur. The agent must use local branches,
bundles or patches and report the remote operation as blocked rather than pretending
it happened.

Provider-specific fork creation beyond `gh` PR tools belongs in a later hosting-provider integration.
