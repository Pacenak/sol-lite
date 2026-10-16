"""Allowlist and first-use confirmation for host repository remotes."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from time import time


def normalize_root(root) -> Path:
    return Path(
        os.path.realpath(os.path.abspath(os.fspath(Path(root).expanduser())))
    )


class RepositoryTrust:
    """Trusted remotes require an allowlisted root and a first-use confirm."""

    def __init__(self, config_roots, state_path: Path):
        self._lock = threading.RLock()
        self._config_roots = [
            normalize_root(item)
            for item in (config_roots or [])
            if str(item).strip()
        ]
        self.state_path = Path(state_path)
        self._extra_roots: list[Path] = []
        self._confirmed: dict[str, float] = {}
        self._load()

    def _load(self) -> None:
        if not self.state_path.is_file():
            return
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return
        if not isinstance(payload, dict):
            return
        roots = payload.get("allowlisted_roots") or []
        if isinstance(roots, list):
            self._extra_roots = [
                normalize_root(item) for item in roots if str(item).strip()
            ]
        confirmed = payload.get("confirmed") or {}
        if isinstance(confirmed, dict):
            self._confirmed = {
                str(normalize_root(key)): float(value)
                for key, value in confirmed.items()
                if str(key).strip()
            }

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "allowlisted_roots": [str(path) for path in self._extra_roots],
            "confirmed": dict(self._confirmed),
        }
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, self.state_path)

    def normalize(self, root) -> Path:
        return normalize_root(root)

    def _allowlist_roots(self) -> list[Path]:
        return [*self._config_roots, *self._extra_roots]

    def is_allowlisted(self, root) -> bool:
        candidate = normalize_root(root)
        for allowed in self._allowlist_roots():
            if candidate == allowed:
                return True
            try:
                candidate.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False

    def is_confirmed(self, root) -> bool:
        return str(normalize_root(root)) in self._confirmed

    def is_trusted(self, root) -> bool:
        path = normalize_root(root)
        return self.is_allowlisted(path) and self.is_confirmed(path)

    def confirm(self, root, *, allowlist_exact: bool = False) -> Path:
        path = normalize_root(root)
        with self._lock:
            if allowlist_exact and path not in self._extra_roots:
                # Exact path allowlist for first-run trust offer.
                if not self.is_allowlisted(path):
                    self._extra_roots.append(path)
            if not self.is_allowlisted(path):
                raise PermissionError(
                    self.explain_denial(path)
                )
            self._confirmed[str(path)] = time()
            self._save()
        return path

    def explain_denial(self, root) -> str:
        path = normalize_root(root)
        if not self.is_allowlisted(path):
            return (
                f"Repository remotes are not allowlisted for {path}. "
                "Add a parent path under repository.trusted_roots in "
                "config/sol-lite.yaml, or accept the first-run trust prompt "
                "when opening this Git workspace."
            )
        if not self.is_confirmed(path):
            return (
                f"Repository remotes for {path} need a one-time trust "
                "confirmation before pull, push, or hosting PR tools run "
                "without repeated remote approval."
            )
        return f"Repository remotes are trusted for {path}."
