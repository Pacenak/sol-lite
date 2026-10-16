"""Allowlist gate for studio SecCheck / lite-pen (authorized hosts only)."""

from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import List, Set

_HOST_RE = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$"
)


def _parse_line(raw: str) -> str | None:
    line = raw.split("#", 1)[0].strip().lower()
    if not line:
        return None
    # strip optional port for membership checks of host part
    host = line.split("/", 1)[0].split(":", 1)[0].strip()
    if not host:
        return None
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass
    if _HOST_RE.match(host):
        return host
    return None


def load_allowlist(path: Path) -> Set[str]:
    if not path.is_file():
        raise FileNotFoundError(f"allowlist missing: {path}")
    hosts: Set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        h = _parse_line(line)
        if h:
            hosts.add(h)
    if not hosts:
        raise ValueError("allowlist is empty — refusing to run")
    return hosts


def assert_target_allowed(target: str, allowed: Set[str]) -> str:
    host = (target or "").strip().lower()
    host = host.split("/", 1)[0].split(":", 1)[0].strip()
    if not host:
        raise ValueError("target required")
    if host not in allowed:
        raise PermissionError(f"target not in allowlist: {host}")
    return host


def require_lab_ack(ack_path: Path) -> None:
    """Lite-pen requires an explicit studio-owner acknowledgement file."""
    if not ack_path.is_file():
        raise PermissionError(
            f"missing {ack_path.name} — copy I_OWN_THIS_LAB.example and keep only on your stick"
        )
    text = ack_path.read_text(encoding="utf-8").strip().upper()
    if "I OWN THIS LAB" not in text and "I_OWN_THIS_LAB" not in text:
        raise PermissionError(
            f"{ack_path.name} must contain the phrase I OWN THIS LAB (studio owner ack)"
        )


def default_ports() -> List[int]:
    return [22, 80, 443, 3000, 8080, 11434]
