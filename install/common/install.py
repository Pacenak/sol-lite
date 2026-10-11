#!/usr/bin/env python3
"""Idempotent SOL-Lite installer/repair helper using only the Python standard library."""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import venv
from datetime import datetime, timezone
from pathlib import Path


def run(command: list[str], root: Path) -> None:
    print("INSTALL:", " ".join(command))
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode:
        raise SystemExit(completed.returncode)


def python_executable(root: Path) -> Path:
    if sys.platform == "win32":
        return root / ".venv" / "Scripts" / "python.exe"
    return root / ".venv" / "bin" / "python"


def state_path(root: Path) -> Path:
    return root / "data" / "state" / "install.json"


def write_state(root: Path, action: str, python_path: Path, voice_report: dict | None = None) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "application": "SOL-Lite",
        "version": "0.2.5",
        "action": action,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python_executable": str(python_path),
        "python_version": platform.python_version(),
        "venv": str(root / ".venv"),
        "install_root": str(root),
        "editable_install": True,
        "launcher": "launcher/windows/SOL-Lite.cmd" if sys.platform == "win32" else "launcher/macos/SOL-Lite.app",
        "voice": voice_report or {},
    }
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def ensure_venv(root: Path) -> Path:
    python_path = python_executable(root)
    if not python_path.is_file():
        print("Creating SOL-Lite virtual environment...")
        venv.create(root / ".venv", with_pip=True)
    if not python_path.is_file():
        raise RuntimeError(f"Virtual environment Python was not created: {python_path}")
    return python_path


def warn_if_kokoro_unsupported(python_path: Path) -> None:
    """Kokoro 0.9 is not published for Python 3.13 or newer."""
    if not python_path.is_file():
        return
    try:
        completed = subprocess.run(
            [str(python_path), "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return
    parts = completed.stdout.split()
    if completed.returncode or len(parts) != 2:
        return
    major, minor = int(parts[0]), int(parts[1])
    if (major, minor) < (3, 13):
        return
    print(
        "INSTALL: Kokoro text-to-speech is not published for Python "
        f"{major}.{minor} (it requires 3.10-3.12). "
        "Speech-to-text will still be installed. "
        "Local text-to-speech stays unavailable in this environment."
    )


def prepare_voice(python_path: Path, root: Path) -> dict:
    """Provision local speech. Prefetch failures are recorded and do not stop install."""
    completed = subprocess.run(
        [str(python_path), "-m", "sol_lite.voice.setup"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    output = "\n".join(part for part in (completed.stdout, completed.stderr) if part).strip()
    errors = []
    if completed.returncode:
        errors.append(output or f"voice setup exited {completed.returncode}")
    elif "needs attention" in output:
        errors.append(output)
    return {"exit_code": completed.returncode, "prefetch_errors": errors, "output": output}


def install(root: Path, *, repair: bool) -> None:
    if sys.version_info < (3, 11):
        raise RuntimeError(f"SOL-Lite requires Python 3.11 or newer; found {platform.python_version()}.")
    python_path = ensure_venv(root)
    warn_if_kokoro_unsupported(python_path)
    run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], root)
    run([str(python_path), "-m", "pip", "install", "-e", ".[dev,voice]"], root)
    voice_report = prepare_voice(python_path, root)
    run([str(python_path), "scripts/preflight.py"], root)
    run([str(python_path), "-m", "sol_lite", "doctor"], root)
    write_state(root, "repair" if repair else "install", python_path, voice_report)
    print("SOL-Lite installation state written:", state_path(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repair", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    install(root, repair=args.repair)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
