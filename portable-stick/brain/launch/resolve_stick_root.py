"""Resolve portable stick roots (BRAIN + optional SOLLITE).

Layout expected::

    SOLBRAIN/                 # encrypted brain (or portable-stick/brain in-repo)
      data/
      workspace/
      launch/resolve_stick_root.py
      settings/
      sec/
      admin-belt/
      models/

    SOLLITE/                  # optional separate volume — Lite clone only
      pyproject.toml          # or sol-lite-src/pyproject.toml
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Union

PathLike = Union[str, Path]


def find_brain_root(start: Optional[PathLike] = None) -> Path:
    """Walk upward until a directory containing ``launch/`` (brain root) is found."""
    cur = Path(start or __file__).resolve()
    if cur.is_file():
        cur = cur.parent
    for _ in range(10):
        if (cur / "launch").is_dir() and cur.name != "launch":
            (cur / "data").mkdir(parents=True, exist_ok=True)
            (cur / "workspace").mkdir(parents=True, exist_ok=True)
            return cur
        if cur.name == "launch" and (cur.parent / "launch").is_dir():
            root = cur.parent
            (root / "data").mkdir(parents=True, exist_ok=True)
            (root / "workspace").mkdir(parents=True, exist_ok=True)
            return root
        if cur.parent == cur:
            break
        cur = cur.parent
    here = Path(__file__).resolve().parent
    root = here.parent
    (root / "data").mkdir(parents=True, exist_ok=True)
    (root / "workspace").mkdir(parents=True, exist_ok=True)
    return root


def _repo_if_lite(path: Path) -> Optional[Path]:
    """Return path if it looks like a PLG_Ai_Lite checkout (has pyproject.toml)."""
    try:
        p = path.resolve()
    except OSError:
        return None
    if not p.is_dir():
        return None
    if (p / "pyproject.toml").is_file():
        return p
    nested = p / "sol-lite-src"
    if (nested / "pyproject.toml").is_file():
        return nested.resolve()
    return None


def _candidate_sollite_dirs(brain: Path) -> Iterable[Path]:
    """Likely mount points / siblings for the SOLLITE volume."""
    seen: List[Path] = []
    out: List[Path] = []

    def add(p: Path) -> None:
        try:
            r = p.resolve()
        except OSError:
            return
        if r in seen:
            return
        seen.append(r)
        out.append(r)

    # Explicit env for the volume root (not the repo)
    vol = os.environ.get("SOL_LITE_VOLUME", "").strip()
    if vol:
        add(Path(vol))

    # Sibling of brain mount (…/SOLBRAIN and …/SOLLITE)
    parent = brain.parent
    add(parent / "SOLLITE")
    if brain.name.upper() in {"SOLBRAIN", "BRAIN"}:
        add(parent / "SOLLITE")

    # Common Linux / macOS automount labels
    media = Path("/media")
    if media.is_dir():
        try:
            for user_dir in media.iterdir():
                add(user_dir / "SOLLITE")
        except OSError:
            pass
    run_media = Path("/run/media")
    if run_media.is_dir():
        try:
            for user_dir in run_media.iterdir():
                add(user_dir / "SOLLITE")
        except OSError:
            pass
    add(Path("/Volumes/SOLLITE"))

    # Windows: check other drive roots for a volume named via folder marker
    if os.name == "nt":
        for letter in "DEFGHIJKLMNOPQRSTUVWXYZ":
            add(Path(f"{letter}:/"))
            add(Path(f"{letter}:/SOLLITE"))

    return out


def find_lite_repo(brain: Optional[PathLike] = None) -> Optional[Path]:
    """Locate PLG_Ai_Lite checkout on SOLLITE, env, or legacy brain/sol-lite-src."""
    existing = os.environ.get("SOL_LITE_REPO", "").strip()
    if existing:
        hit = _repo_if_lite(Path(existing))
        if hit is not None:
            return hit
        # Allow pointing directly at repo root even if layout check is soft
        p = Path(existing).resolve()
        if p.is_dir():
            return p

    brain_root = Path(brain).resolve() if brain is not None else find_brain_root()

    legacy = _repo_if_lite(brain_root / "sol-lite-src")
    if legacy is not None:
        return legacy
    if (brain_root / "sol-lite-src" / "pyproject.toml").is_file():
        return (brain_root / "sol-lite-src").resolve()

    for cand in _candidate_sollite_dirs(brain_root):
        hit = _repo_if_lite(cand)
        if hit is not None:
            return hit

    return None


def env_for_brain(root: Optional[PathLike] = None) -> Dict[str, str]:
    if root is not None:
        brain = Path(root).resolve()
        (brain / "data").mkdir(parents=True, exist_ok=True)
        (brain / "workspace").mkdir(parents=True, exist_ok=True)
    else:
        brain = find_brain_root()
    settings = brain / "settings" / "settings.yaml"
    out: Dict[str, str] = {
        "SOL_DATA_ROOT": str((brain / "data").resolve()),
        "SOL_WORKSPACE_ROOT": str((brain / "workspace").resolve()),
    }
    if settings.is_file():
        out["SOL_LITE_SETTINGS_FILE"] = str(settings.resolve())
    out["SOL_OLLAMA_URL"] = os.environ.get("SOL_OLLAMA_URL") or "http://127.0.0.1:11434"

    lite = find_lite_repo(brain)
    if lite is not None:
        out["SOL_LITE_REPO"] = str(lite)

    # Owner unlock for sol_studio_admin — only when BRAIN carries the ack file.
    ack = brain / "sec" / "I_OWN_THIS_LAB"
    unlock = brain / "data" / "state" / "studio_owner.unlock"
    if ack.is_file() or unlock.is_file():
        out["SOL_STUDIO_ADMIN_FEATURE"] = (
            os.environ.get("SOL_STUDIO_ADMIN_FEATURE") or "1"
        )
        out["SOL_STUDIO_OWNER"] = os.environ.get("SOL_STUDIO_OWNER") or "1"
        owner_file = unlock if unlock.is_file() else ack
        try:
            text = owner_file.read_text(encoding="utf-8")
        except OSError:
            text = ""
        for line in text.splitlines():
            if line.strip().lower().startswith("owner_id:"):
                oid = line.split(":", 1)[-1].strip()
                if oid:
                    out["SOL_STUDIO_OWNER_ID"] = os.environ.get("SOL_STUDIO_OWNER_ID") or oid
                break
    return out


def apply_env(root: Optional[PathLike] = None) -> Dict[str, str]:
    mapping = env_for_brain(root)
    os.environ.update(mapping)
    return mapping


if __name__ == "__main__":
    m = apply_env()
    for k, v in sorted(m.items()):
        print(f"{k}={v}")
