"""Safe Git repository operations for local and offline engineering work."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ..core.exceptions import ToolExecutionError
from ..permissions.scopes import REPOSITORY_READ, REPOSITORY_REMOTE, REPOSITORY_WRITE
from ..security.path_guard import resolve_workspace_path
from .base import ToolDefinition


def _repo_path(ctx, value: str | None = None) -> Path:
    root = Path(ctx.workspace_root).resolve()
    candidate = resolve_workspace_path(value or ".", root, must_exist=True)
    if not candidate.is_dir():
        raise NotADirectoryError(candidate)
    completed = _run_git(["-C", str(candidate), "rev-parse", "--show-toplevel"], cwd=root)
    repo = Path(completed.stdout.strip()).resolve()
    try:
        repo.relative_to(root)
    except ValueError as exc:
        raise ToolExecutionError("Git repository is outside the approved workspace.") from exc
    return repo


def _git_executable() -> str:
    executable = shutil.which("git")
    if executable is None:
        raise ToolExecutionError("Git executable was not found on PATH.")
    return executable


def _run_git(
    args: list[str], *, cwd: Path, timeout: float = 120.0
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [_git_executable(), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
        raise ToolExecutionError(f"Git execution failed: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise ToolExecutionError(f"git {' '.join(args)} failed ({result.returncode}): {detail}")
    return result


def _audit(ctx, event: str, **data) -> None:
    ctx.audit.record(event, **data)


def _approval(ctx, scope: str, *, approval_id, operation, target, arguments, plan) -> None:
    ctx.permission_engine.check(
        scope,
        approval_id=approval_id,
        operation=operation,
        target=target,
        arguments=arguments,
        plan=plan,
    )


def _branch(repo: Path) -> str | None:
    result = _run_git(["-C", str(repo), "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=repo)
    return result.stdout.strip() or None


def _current_commit(repo: Path) -> str:
    return _run_git(["-C", str(repo), "rev-parse", "HEAD"], cwd=repo).stdout.strip()


def _has_commit(repo: Path) -> bool:
    try:
        _current_commit(repo)
    except ToolExecutionError:
        return False
    return True


def _safe_remote(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc:
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    if "@" in value and ":" in value.split("@", 1)[0]:
        return value.split("@", 1)[1]
    return value


def _reject_embedded_credentials(value: str) -> None:
    parsed = urlsplit(value)
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Embedded credentials in Git URLs are not allowed; use SSH or a credential helper.")


def repository_status(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    _approval(ctx, REPOSITORY_READ, approval_id=None, operation="repository_status",
              target=str(repo), arguments={"path": str(repo)}, plan="")
    branch = _branch(repo)
    status = _run_git(["-C", str(repo), "status", "--porcelain=v1", "--branch"], cwd=repo).stdout
    upstream = ""
    try:
        upstream = _run_git(
            ["-C", str(repo), "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
            cwd=repo,
        ).stdout.strip()
    except ToolExecutionError:
        upstream = ""
    result = {
        "repository": str(repo),
        "branch": branch,
        "detached": branch is None,
        "head": _current_commit(repo) if _has_commit(repo) else None,
        "upstream": upstream or None,
        "porcelain": status,
        "clean": status.splitlines()[1:] == [] if status.startswith("##") else not bool(status.strip()),
    }
    _audit(ctx, "repository.status", repository=str(repo), branch=branch, clean=result["clean"])
    return result


def repository_diff(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    _approval(ctx, REPOSITORY_READ, approval_id=None, operation="repository_diff",
              target=str(repo), arguments={"path": str(repo)}, plan="")
    staged = bool(args.get("staged", False))
    base = ["-C", str(repo), "diff", "--no-ext-diff", "--binary"]
    if staged:
        base.append("--cached")
    result = _run_git(base, cwd=repo)
    return {"repository": str(repo), "staged": staged, "diff": result.stdout}


def repository_log(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    _approval(ctx, REPOSITORY_READ, approval_id=None, operation="repository_log",
              target=str(repo), arguments={"path": str(repo)}, plan="")
    limit = max(1, min(int(args.get("limit", 20)), 200))
    result = _run_git(
        ["-C", str(repo), "log", f"-{limit}", "--date=iso-strict",
         "--format=%H%x09%an%x09%ad%x09%s"], cwd=repo,
    )
    commits = []
    for line in result.stdout.splitlines():
        commit, author, date, subject = line.split("\t", 3)
        commits.append({"commit": commit, "author": author, "date": date, "subject": subject})
    return {"repository": str(repo), "commits": commits}


def repository_branches(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    _approval(ctx, REPOSITORY_READ, approval_id=None, operation="repository_branches",
              target=str(repo), arguments={"path": str(repo)}, plan="")
    result = _run_git(
        ["-C", str(repo), "for-each-ref", "--format=%(refname:short)\t%(objectname)", "refs/heads"],
        cwd=repo,
    )
    branches = []
    current = _branch(repo)
    for line in result.stdout.splitlines():
        name, commit = line.split("\t", 1)
        branches.append({"name": name, "commit": commit, "current": name == current})
    return {"repository": str(repo), "branches": branches}


def repository_remotes(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    _approval(ctx, REPOSITORY_READ, approval_id=None, operation="repository_remotes",
              target=str(repo), arguments={"path": str(repo)}, plan="")
    result = _run_git(["-C", str(repo), "remote", "-v"], cwd=repo)
    remotes = []
    for line in result.stdout.splitlines():
        name, rest = line.split("\t", 1)
        url, kind = rest.rsplit(" (", 1)
        remotes.append({"name": name, "url": _safe_remote(url), "kind": kind[:-1]})
    return {"repository": str(repo), "remotes": remotes}


def repository_create_branch(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    name = str(args["name"])
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", name) or name.startswith("/") or name.endswith("/"):
        raise ValueError("Invalid Git branch name.")
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "name": name, "start_point": args.get("start_point")}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_create_branch",
              target=str(repo), arguments=arguments, plan=plan)
    command = ["-C", str(repo), "switch", "-c", name]
    if args.get("start_point"):
        command.append(str(args["start_point"]))
    _run_git(command, cwd=repo)
    _audit(ctx, "repository.branch_create", repository=str(repo), branch=name)
    return {"repository": str(repo), "branch": name, "commit": _current_commit(repo)}


def repository_checkout(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    name = str(args["branch"])
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "branch": name}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_checkout",
              target=str(repo), arguments=arguments, plan=plan)
    status = _run_git(["-C", str(repo), "status", "--porcelain"], cwd=repo).stdout
    if status.strip() and not bool(args.get("allow_dirty", False)):
        raise ToolExecutionError("Refusing checkout with uncommitted changes; inspect or commit first.")
    _run_git(["-C", str(repo), "switch", name], cwd=repo)
    _audit(ctx, "repository.checkout", repository=str(repo), branch=name)
    return {"repository": str(repo), "branch": _branch(repo), "commit": _current_commit(repo)}


def repository_stage(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    paths = [str(p) for p in args["paths"]]
    if not paths:
        raise ValueError("At least one path is required.")
    root = Path(ctx.workspace_root).resolve()
    safe_paths = [resolve_workspace_path(p, root, must_exist=True) for p in paths]
    relative = [p.relative_to(repo).as_posix() for p in safe_paths]
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "paths": relative}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_stage",
              target=str(repo), arguments=arguments, plan=plan)
    _run_git(["-C", str(repo), "add", "--", *relative], cwd=repo)
    _audit(ctx, "repository.stage", repository=str(repo), paths=relative)
    return {"repository": str(repo), "staged": relative}


def repository_commit(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    message = str(args["message"]).strip()
    if not message:
        raise ValueError("Commit message cannot be empty.")
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "message": message}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_commit",
              target=str(repo), arguments=arguments, plan=plan)
    _run_git(["-C", str(repo), "commit", "-m", message], cwd=repo)
    commit = _current_commit(repo)
    _audit(ctx, "repository.commit", repository=str(repo), commit=commit)
    return {"repository": str(repo), "commit": commit, "branch": _branch(repo)}


def repository_create_bundle(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    output = resolve_workspace_path(args["output"], Path(ctx.workspace_root).resolve())
    if output.exists():
        raise FileExistsError(output)
    branch = _branch(repo)
    ref = f"refs/heads/{branch}" if branch else "HEAD"
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "output": str(output), "ref": ref}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_create_bundle",
              target=str(output), arguments=arguments, plan=plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["-C", str(repo), "bundle", "create", str(output), ref], cwd=repo)
    _run_git(["-C", str(repo), "bundle", "verify", str(output)], cwd=repo)
    _audit(ctx, "repository.bundle_create", repository=str(repo), output=str(output), ref=ref)
    return {"repository": str(repo), "bundle": str(output), "ref": ref, "commit": _current_commit(repo)}


def repository_import_bundle(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    bundle = resolve_workspace_path(args["bundle"], Path(ctx.workspace_root).resolve(), must_exist=True)
    if not bundle.is_file():
        raise FileNotFoundError(bundle)
    branch = str(args["branch"])
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        raise ValueError("Invalid Git branch name.")
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "bundle": str(bundle), "branch": branch}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_import_bundle",
              target=str(repo), arguments=arguments, plan=plan)
    verify = _run_git(["-C", str(repo), "bundle", "verify", str(bundle)], cwd=repo)
    import_ref = f"refs/remotes/sol-offline/{branch}"
    _run_git(["-C", str(repo), "fetch", str(bundle), f"refs/heads/{branch}:{import_ref}"], cwd=repo)
    _audit(ctx, "repository.bundle_import", repository=str(repo), bundle=str(bundle), ref=import_ref)
    return {"repository": str(repo), "bundle": str(bundle), "import_ref": import_ref,
            "verify": verify.stdout.strip()}


def repository_create_patch(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    output = resolve_workspace_path(args["output"], Path(ctx.workspace_root).resolve())
    if output.exists():
        raise FileExistsError(output)
    staged = bool(args.get("staged", False))
    arguments = {"path": str(repo), "output": str(output), "staged": staged}
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_create_patch",
              target=str(output), arguments=arguments, plan=plan)
    command = ["-C", str(repo), "diff", "--no-ext-diff", "--binary"]
    if staged:
        command.append("--cached")
    result = _run_git(command, cwd=repo)
    if not result.stdout:
        raise ToolExecutionError("Git diff is empty; there are no changes to export as a patch.")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.stdout, encoding="utf-8", newline="")
    _audit(ctx, "repository.patch_create", repository=str(repo), output=str(output), staged=staged)
    return {"repository": str(repo), "patch": str(output), "staged": staged,
            "bytes": output.stat().st_size}


def repository_merge_import(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    branch = str(args["branch"])
    import_ref = f"refs/remotes/sol-offline/{branch}"
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "branch": branch, "import_ref": import_ref}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_merge_import",
              target=str(repo), arguments=arguments, plan=plan)
    status = _run_git(["-C", str(repo), "status", "--porcelain"], cwd=repo).stdout
    if status.strip():
        raise ToolExecutionError("Refusing offline merge with uncommitted changes.")
    current = _branch(repo)
    if current != branch:
        raise ToolExecutionError(f"Current branch is {current!r}; checkout {branch!r} before merging.")
    _run_git(["-C", str(repo), "merge", "--ff-only", import_ref], cwd=repo)
    commit = _current_commit(repo)
    _audit(ctx, "repository.offline_merge", repository=str(repo), branch=branch, commit=commit)
    return {"repository": str(repo), "branch": branch, "commit": commit, "merged": True}


def repository_apply_patch(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    patch = resolve_workspace_path(args["patch"], Path(ctx.workspace_root).resolve(), must_exist=True)
    if not patch.is_file():
        raise FileNotFoundError(patch)
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "patch": str(patch)}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_apply_patch",
              target=str(repo), arguments=arguments, plan=plan)
    _run_git(["-C", str(repo), "apply", "--check", str(patch)], cwd=repo)
    _run_git(["-C", str(repo), "apply", "--index", str(patch)], cwd=repo)
    _audit(ctx, "repository.patch_apply", repository=str(repo), patch=str(patch))
    return {"repository": str(repo), "patch": str(patch), "applied": True, "staged": True}


def repository_set_remote(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    name = str(args["name"])
    url = str(args["url"])
    _reject_embedded_credentials(url)
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name):
        raise ValueError("Invalid Git remote name.")
    safe_url = _safe_remote(url)
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "name": name, "url": safe_url}
    _approval(ctx, REPOSITORY_REMOTE, approval_id=approval_id, operation="repository_set_remote",
              target=safe_url, arguments=arguments, plan=plan)
    remotes = _run_git(["-C", str(repo), "remote"], cwd=repo).stdout.splitlines()
    if name in remotes:
        _run_git(["-C", str(repo), "remote", "set-url", name, url], cwd=repo)
    else:
        _run_git(["-C", str(repo), "remote", "add", name, url], cwd=repo)
    _audit(ctx, "repository.remote_set", repository=str(repo), remote=name, url=safe_url)
    return {"repository": str(repo), "remote": name, "url": safe_url}


def repository_fetch(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    remote = str(args.get("remote", "origin"))
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "remote": remote}
    _approval(ctx, REPOSITORY_REMOTE, approval_id=approval_id, operation="repository_fetch",
              target=remote, arguments=arguments, plan=plan)
    _run_git(["-C", str(repo), "fetch", "--prune", remote], cwd=repo)
    _audit(ctx, "repository.fetch", repository=str(repo), remote=remote)
    return {"repository": str(repo), "remote": remote, "fetched": True}


def repository_push(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    remote = str(args.get("remote", "origin"))
    branch = str(args.get("branch") or _branch(repo) or "")
    if not branch:
        raise ValueError("A branch is required when HEAD is detached.")
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "remote": remote, "branch": branch}
    _approval(ctx, REPOSITORY_REMOTE, approval_id=approval_id, operation="repository_push",
              target=remote, arguments=arguments, plan=plan)
    _run_git(["-C", str(repo), "push", remote, branch], cwd=repo)
    _audit(ctx, "repository.push", repository=str(repo), remote=remote, branch=branch)
    return {"repository": str(repo), "remote": remote, "branch": branch, "pushed": True}


def repository_clone_local(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    source = Path(str(args["source"])).expanduser().resolve()
    destination = resolve_workspace_path(args["destination"], root)
    if destination.exists():
        raise FileExistsError(destination)
    if not (source / ".git").exists() and not (source / "HEAD").exists():
        raise ToolExecutionError("Source does not appear to be a Git working tree or bare repository.")
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"source": str(source), "destination": str(destination)}
    _approval(ctx, REPOSITORY_WRITE, approval_id=approval_id, operation="repository_clone_local",
              target=str(destination), arguments=arguments, plan=plan)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["clone", "--no-hardlinks", str(source), str(destination)], cwd=root)
    _audit(ctx, "repository.clone_local", source=str(source), destination=str(destination))
    return {"source": str(source), "repository": str(destination), "offline": True}


def repository_clone_remote(ctx, args):
    root = Path(ctx.workspace_root).resolve()
    url = str(args["url"])
    _reject_embedded_credentials(url)
    destination = resolve_workspace_path(args["destination"], root)
    if destination.exists():
        raise FileExistsError(destination)
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"url": _safe_remote(url), "destination": str(destination)}
    _approval(ctx, REPOSITORY_REMOTE, approval_id=approval_id, operation="repository_clone_remote",
              target=_safe_remote(url), arguments=arguments, plan=plan)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run_git(["clone", url, str(destination)], cwd=root)
    _audit(ctx, "repository.clone_remote", destination=str(destination), remote=_safe_remote(url))
    return {"repository": str(destination), "remote": _safe_remote(url), "offline": False}


def repository_tools():
    approval = {
        "plan": {"type": "string"},
        "approval_id": {"type": "string"},
    }
    return [
        ToolDefinition("repository_status", "Inspect Git repository state without modifying it.",
                        {"type": "object", "properties": {"path": {"type": "string"}}}, repository_status),
        ToolDefinition("repository_diff", "Read a Git diff without modifying the repository.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "staged": {"type": "boolean"},
                        }}, repository_diff),
        ToolDefinition("repository_log", "Read recent Git commits.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                        }}, repository_log),
        ToolDefinition("repository_branches", "List local Git branches.",
                        {"type": "object", "properties": {"path": {"type": "string"}}}, repository_branches),
        ToolDefinition("repository_remotes", "List Git remotes with credentials redacted.",
                        {"type": "object", "properties": {"path": {"type": "string"}}}, repository_remotes),
        ToolDefinition("repository_create_branch", "Create a local Git branch after exact human approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "name": {"type": "string"},
                            "start_point": {"type": "string"}, **approval,
                        }, "required": ["name", "plan", "approval_id"]}, repository_create_branch),
        ToolDefinition("repository_checkout", "Switch branches without discarding dirty changes.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "branch": {"type": "string"}, **approval,
                        }, "required": ["branch", "plan", "approval_id"]}, repository_checkout),
        ToolDefinition("repository_stage", "Stage exact repository paths after approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "paths": {"type": "array", "items": {"type": "string"}}, **approval,
                        }, "required": ["paths", "plan", "approval_id"]}, repository_stage),
        ToolDefinition("repository_commit", "Create a local Git commit after exact approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "message": {"type": "string"}, **approval,
                        }, "required": ["message", "plan", "approval_id"]}, repository_commit),
        ToolDefinition("repository_create_bundle", "Create and verify an offline Git bundle for transport.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "output": {"type": "string"}, **approval,
                        }, "required": ["output", "plan", "approval_id"]}, repository_create_bundle),
        ToolDefinition("repository_import_bundle", "Verify an offline Git bundle and import it as a review ref.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "bundle": {"type": "string"},
                            "branch": {"type": "string"}, **approval,
                        }, "required": ["bundle", "branch", "plan", "approval_id"]}, repository_import_bundle),
        ToolDefinition("repository_create_patch", "Create a binary-capable Git patch for offline transport.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "output": {"type": "string"},
                            "staged": {"type": "boolean"}, **approval,
                        }, "required": ["output", "plan", "approval_id"]}, repository_create_patch),
        ToolDefinition("repository_merge_import", "Fast-forward the current branch to a previously imported offline ref.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "branch": {"type": "string"}, **approval,
                        }, "required": ["branch", "plan", "approval_id"]}, repository_merge_import),
        ToolDefinition("repository_apply_patch", "Check and apply a patch with the index updated.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "patch": {"type": "string"}, **approval,
                        }, "required": ["patch", "plan", "approval_id"]}, repository_apply_patch),
        ToolDefinition("repository_set_remote", "Add or update a Git remote after remote approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "name": {"type": "string"},
                            "url": {"type": "string"}, **approval,
                        }, "required": ["name", "url", "plan", "approval_id"]}, repository_set_remote),
        ToolDefinition("repository_fetch", "Fetch from a remote; requires repository and network approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "remote": {"type": "string"}, **approval,
                        }, "required": ["plan", "approval_id"]}, repository_fetch),
        ToolDefinition("repository_push", "Push a branch to a remote; requires repository and network approval.",
                        {"type": "object", "properties": {
                            "path": {"type": "string"}, "remote": {"type": "string"},
                            "branch": {"type": "string"}, **approval,
                        }, "required": ["plan", "approval_id"]}, repository_push),
        ToolDefinition("repository_clone_remote", "Clone a remote Git repository after repository remote approval.",
                        {"type": "object", "properties": {
                            "url": {"type": "string"}, "destination": {"type": "string"}, **approval,
                        }, "required": ["url", "destination", "plan", "approval_id"]}, repository_clone_remote),
        ToolDefinition("repository_clone_local", "Clone a local repository without network access.",
                        {"type": "object", "properties": {
                            "source": {"type": "string"}, "destination": {"type": "string"}, **approval,
                        }, "required": ["source", "destination", "plan", "approval_id"]}, repository_clone_local),
    ]
