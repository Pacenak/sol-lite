# Repository Workflows

SOL-Lite can work on a Git repository locally without network access. Remote synchronization is
a separate capability and is disabled by default.

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

- clone it with `repository_clone_remote` when remote access is explicitly enabled;
- inspect and edit it locally;
- set or update its remote with `repository_set_remote`;
- fetch changes with `repository_fetch`; and
- push an approved branch with `repository_push`.

If the machine is offline, remote operations cannot occur. The agent must use local branches,
bundles or patches and report the remote operation as `[UNKNOWN]` or blocked rather than pretending
it happened.

Provider-specific fork creation and pull-request APIs belong in a later hosting-provider integration.
