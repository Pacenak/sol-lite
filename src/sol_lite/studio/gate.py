"""Facts the studio tools can check without guessing a host or a secret."""
from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from ..core.exceptions import ToolExecutionError

_HOST = re.compile(r"\b(?:\d{1,3}(?:\.\d{1,3}){3}|(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,})\b")
_SECRET = re.compile(r"\{\{([A-Za-z0-9_]+)\}\}")
_UNSAFE_PATH = re.compile(r"[\x00\r\n;|&$`<>]")
_DONE = re.compile(r"(?i)\b(?:i completed|i've completed|it is done)\b")
_DONE_EXACT = re.compile(r"(?i)(?:yes|done|completed|finished)\.?")


def explicit_completion(text: str) -> bool:
    trimmed = " ".join((text or "").split())
    if _DONE_EXACT.fullmatch(trimmed):
        return True
    return _DONE.search(trimmed) is not None


def bind_hosts(command: str, nodes) -> dict:
    """A host is bound only when it equals an enabled node's id or hostname."""
    enabled = set()
    for node in nodes:
        if getattr(node, "enabled", True):
            enabled.add(str(node.hostname))
            enabled.add(str(node.id))
    found = []
    for match in _HOST.findall(command or ""):
        if match not in found:
            found.append(match)
    return {
        "bound": [item for item in found if item in enabled],
        "unbound": [item for item in found if item not in enabled],
        "secrets": _SECRET.findall(command or ""),
    }


def http_host_allowed(url: str, nodes) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        return False
    host = (parsed.hostname or "").casefold()
    allowed = {"localhost", "127.0.0.1"}
    for node in nodes:
        if getattr(node, "enabled", True) and getattr(node, "hostname", ""):
            allowed.add(str(node.hostname).casefold())
    return host in allowed


def safe_remote_path(path: str) -> str:
    text = str(path or "").strip()
    if not text or text.startswith("-") or ".." in text.split("/") or ".." in text.split("\\"):
        raise ValueError("Remote path is not safe to address.")
    if _UNSAFE_PATH.search(text):
        raise ValueError("Remote path is not safe to address.")
    return text


def safe_probe_host(hostname: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._:-]+", hostname or ""):
        raise ValueError("Host name is not safe to probe.")
    return hostname


def snapshot_relative(path: str) -> Path:
    text = str(path).replace("\\", "/")
    if len(text) >= 2 and text[1] == ":":
        text = text[2:]
    parts = [part for part in text.split("/") if part not in {"", ".", ".."}]
    if not parts:
        raise ValueError("Snapshot path is empty.")
    return Path(*parts)


def write_snapshot(state_root: Path, host: str, relative: Path, data: bytes) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    destination = Path(state_root) / "backups" / host / stamp / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.write_bytes(data)
    written = partial.read_bytes()
    if hashlib.sha256(written).hexdigest() != hashlib.sha256(data).hexdigest():
        partial.unlink(missing_ok=True)
        raise ToolExecutionError("Snapshot hash did not match the source bytes.")
    partial.replace(destination)
    return destination


def git_tracks(root: Path, path: Path) -> bool:
    try:
        relative = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative.as_posix()],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def snapshot_untracked(ctx, path: Path) -> str | None:
    """Copy a file that Git does not track. Tracked files return None."""
    root = Path(ctx.workspace_root).resolve()
    if git_tracks(root, path):
        return None
    state_root = getattr(ctx, "state_root", None)
    if not state_root:
        raise ToolExecutionError("Untracked file edit requires the SOL-Lite state directory.")
    relative = snapshot_relative(str(path.resolve().relative_to(root)))
    destination = write_snapshot(Path(state_root), "local", relative, path.read_bytes())
    return str(destination)
