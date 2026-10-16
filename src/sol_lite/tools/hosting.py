"""GitHub hosting PR tools via the host ``gh`` CLI."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ..core.exceptions import ToolExecutionError
from ..permissions.scopes import REPOSITORY_WRITE
from .repository import _audit, _approval, _repo_path, _require_remote


def _gh_executable() -> str:
    executable = shutil.which("gh")
    if executable is None:
        raise ToolExecutionError(
            "GitHub CLI (gh) was not found on PATH. Install gh and run "
            "`gh auth login` to use hosting PR tools. Local git tools still work."
        )
    return executable


def _run_gh(
    args: list[str],
    *,
    cwd: Path,
    timeout: float = 120.0,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            [_gh_executable(), *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
        raise ToolExecutionError(f"gh execution failed: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown gh error"
        if "not logged" in detail.casefold() or "auth" in detail.casefold():
            raise ToolExecutionError(
                f"gh authentication required ({detail}). Run `gh auth login`."
            )
        raise ToolExecutionError(f"gh {' '.join(args)} failed ({result.returncode}): {detail}")
    return result


def hosting_pr_create(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    title = str(args["title"]).strip()
    if not title:
        raise ValueError("PR title cannot be empty.")
    body = str(args.get("body") or "")
    base = str(args.get("base") or "main")
    head = str(args.get("head") or "").strip() or None
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {
        "path": str(repo),
        "title": title,
        "base": base,
        "head": head,
    }
    _require_remote(
        ctx,
        repo,
        approval_id=approval_id,
        operation="hosting_pr_create",
        target=str(repo),
        arguments=arguments,
        plan=plan,
    )
    command = [
        "pr",
        "create",
        "--title",
        title,
        "--body",
        body,
        "--base",
        base,
    ]
    if head:
        command.extend(["--head", head])
    result = _run_gh(command, cwd=repo)
    url = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    _audit(ctx, "hosting.pr_create", repository=str(repo), title=title, url=url)
    return {"repository": str(repo), "title": title, "base": base, "url": url, "created": True}


def hosting_pr_status(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo)}
    _require_remote(
        ctx,
        repo,
        approval_id=approval_id,
        operation="hosting_pr_status",
        target=str(repo),
        arguments=arguments,
        plan=plan,
    )
    result = _run_gh(
        [
            "pr",
            "view",
            "--json",
            "number,title,state,url,mergeable,statusCheckRollup,headRefName,baseRefName",
        ],
        cwd=repo,
    )
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise ToolExecutionError("gh returned non-JSON PR status.") from exc
    _audit(ctx, "hosting.pr_status", repository=str(repo), number=payload.get("number"))
    return {"repository": str(repo), "pull_request": payload}


def hosting_pr_merge(ctx, args):
    repo = _repo_path(ctx, args.get("path"))
    method = str(args.get("method", "merge")).strip().lower() or "merge"
    if method not in {"merge", "squash", "rebase"}:
        raise ValueError("method must be merge, squash, or rebase.")
    plan = str(args.get("plan", ""))
    approval_id = args.get("approval_id")
    arguments = {"path": str(repo), "method": method}
    _require_remote(
        ctx,
        repo,
        approval_id=approval_id,
        operation="hosting_pr_merge",
        target=str(repo),
        arguments=arguments,
        plan=plan,
    )
    _approval(
        ctx,
        REPOSITORY_WRITE,
        approval_id=approval_id,
        operation="hosting_pr_merge",
        target=str(repo),
        arguments=arguments,
        plan=plan,
    )
    flag = {"merge": "--merge", "squash": "--squash", "rebase": "--rebase"}[method]
    _run_gh(["pr", "merge", flag, "--delete-branch=false"], cwd=repo)
    _audit(ctx, "hosting.pr_merge", repository=str(repo), method=method)
    return {"repository": str(repo), "method": method, "merged": True}


def hosting_tools():
    approval = {
        "plan": {"type": "string"},
        "approval_id": {"type": "string"},
    }
    from .base import ToolDefinition

    return [
        ToolDefinition(
            "hosting_pr_create",
            "Create a GitHub pull request with gh for the trusted workspace repository.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "base": {"type": "string"},
                    "head": {"type": "string"},
                    **approval,
                },
                "required": ["title", "plan", "approval_id"],
            },
            hosting_pr_create,
        ),
        ToolDefinition(
            "hosting_pr_status",
            "Show the open GitHub pull request status via gh.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    **approval,
                },
                "required": ["plan", "approval_id"],
            },
            hosting_pr_status,
        ),
        ToolDefinition(
            "hosting_pr_merge",
            "Merge the open GitHub pull request via gh after exact approval.",
            {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "method": {
                        "type": "string",
                        "enum": ["merge", "squash", "rebase"],
                    },
                    **approval,
                },
                "required": ["plan", "approval_id"],
            },
            hosting_pr_merge,
        ),
    ]
