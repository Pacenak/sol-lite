"""Read a short project brief from workspace manifests."""
from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from ..core.exceptions import PermissionDenied, SecurityError
from ..tools.filesystem import inventory_workspace, read_workspace_file

_NAME_FIRST = (
    "readme.md",
    "readme.txt",
    "readme.rst",
    "readme",
    "package.json",
    "pyproject.toml",
    "cargo.toml",
)
_MANIFEST_SUFFIXES = (".sln", ".csproj", ".fsproj")
_TOOL_ERROR = re.compile(
    r"not a git repository|fatal:\s|git .+ failed \(|tool execution failed",
    re.IGNORECASE,
)
_EMPTY_ACK = re.compile(
    r"you(?:'ve| have) provided|you pasted|"
    r"let me know how i can assist|"
    r"reviewed the (?:workspace )?structure",
    re.IGNORECASE,
)
_HEADING = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_CARGO_NAME = re.compile(r'(?m)^name\s*=\s*"([^"]+)"')
_CARGO_DESCRIPTION = re.compile(r'(?m)^description\s*=\s*"([^"]+)"')
_ASSEMBLY = re.compile(r"<AssemblyName>\s*([^<]+?)\s*</AssemblyName>")


def _rank(path: str) -> tuple[int, str]:
    name = Path(path).name.casefold()
    if name in _NAME_FIRST:
        return (_NAME_FIRST.index(name), path)
    if name.endswith(_MANIFEST_SUFFIXES):
        return (len(_NAME_FIRST), path)
    return (len(_NAME_FIRST) + 1, path)


def _excerpt(text: str, limit: int = 500) -> str:
    compact = " ".join(str(text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _paragraph(text: str, limit: int = 400) -> str:
    lines = []
    for line in str(text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if lines:
                break
            continue
        lines.append(stripped)
        if len(" ".join(lines)) >= limit:
            break
    return " ".join(lines)[:limit]


def _json_fields(text: str) -> tuple[str | None, str | None]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, None
    if not isinstance(data, dict):
        return None, None
    name = data.get("name")
    description = data.get("description")
    return (
        name if isinstance(name, str) and name.strip() else None,
        description if isinstance(description, str) and description.strip() else None,
    )


def _pyproject_fields(text: str) -> tuple[str | None, str | None]:
    try:
        data = tomllib.loads(text)
    except (tomllib.TOMLDecodeError, ValueError):
        return None, None
    project = data.get("project") if isinstance(data, dict) else None
    if not isinstance(project, dict):
        return None, None
    name = project.get("name")
    description = project.get("description")
    return (
        name if isinstance(name, str) and name.strip() else None,
        description if isinstance(description, str) and description.strip() else None,
    )


def _named_fields(path: str, text: str) -> tuple[str | None, str | None]:
    name = Path(path).name.casefold()
    if name == "package.json":
        return _json_fields(text)
    if name == "pyproject.toml":
        return _pyproject_fields(text)
    if name == "cargo.toml":
        found = _CARGO_NAME.search(text or "")
        described = _CARGO_DESCRIPTION.search(text or "")
        return (
            found.group(1) if found else None,
            described.group(1) if described else None,
        )
    if name.endswith(_MANIFEST_SUFFIXES):
        assembly = _ASSEMBLY.search(text or "")
        return (assembly.group(1).strip() if assembly else Path(path).stem), None
    if name.startswith("readme"):
        heading = _HEADING.search(text or "")
        return (heading.group(1).strip() if heading else None), _paragraph(text)
    return None, None


def build_project_brief(ctx) -> dict:
    """Inventory the workspace and read at most four manifests."""
    overview = inventory_workspace(ctx, {})
    manifests = sorted(
        [path for path in overview.get("manifests") or [] if isinstance(path, str)],
        key=_rank,
    )[:4]
    excerpts = []
    structured_name = None
    heading_name = None
    purpose = None
    for path in manifests:
        try:
            loaded = read_workspace_file(ctx, {"path": path})
        except (OSError, UnicodeError, ValueError, PermissionDenied, SecurityError):
            continue
        text = str(loaded.get("content") or "")
        found_name, found_purpose = _named_fields(path, text)
        if Path(path).name.casefold().startswith("readme"):
            if heading_name is None and found_name:
                heading_name = found_name.strip()
        elif structured_name is None and found_name:
            structured_name = found_name.strip()
        if purpose is None and found_purpose:
            purpose = found_purpose.strip()
        excerpts.append({"path": path, "excerpt": _excerpt(text)})
    root = Path(ctx.workspace_root)
    name = structured_name or heading_name or root.name or str(root)
    return {
        "name": name,
        "purpose": purpose or "",
        "top_level": [
            item for item in overview.get("top_level") or [] if isinstance(item, str)
        ],
        "extensions": overview.get("extensions") or {},
        "count": overview.get("count", 0),
        "manifests": excerpts,
    }


def format_project_brief(brief: dict) -> str:
    """Plain-text brief a local model can repeat without the raw file list."""
    lines = [f"Project name: {brief.get('name') or 'unknown'}"]
    purpose = str(brief.get("purpose") or "").strip()
    if purpose:
        lines.append(f"Purpose: {purpose}")
    top = [item for item in brief.get("top_level") or [] if isinstance(item, str)]
    lines.append("Top level: " + (", ".join(top) if top else "(none)"))
    if brief.get("count") is not None:
        lines.append(f"Files: {brief['count']}")
    for item in brief.get("manifests") or []:
        path = item.get("path")
        excerpt = item.get("excerpt")
        if path:
            lines.append(f"Manifest {path}: {excerpt}")
    return "\n".join(lines)


def identity_answer_misses(content: str, brief: dict) -> bool:
    """True when the draft is an error, an empty acknowledgement, or ungrounded."""
    text = content or ""
    if _TOOL_ERROR.search(text) or _EMPTY_ACK.search(text):
        return True
    lowered = text.casefold()
    name = str(brief.get("name") or "").strip()
    if name and name.casefold() in lowered:
        return False
    for entry in brief.get("top_level") or []:
        token = str(entry).strip().strip("/").casefold()
        if len(token) >= 2 and token in lowered:
            return False
    return True
