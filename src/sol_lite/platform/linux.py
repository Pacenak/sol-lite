"""Linux shell adapter.

Uses the user's installed POSIX shells and does not elevate privileges.
Privilege escalation is deliberately outside the platform adapter.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import PlatformAdapter


class LinuxAdapter(PlatformAdapter):
    name = "linux"

    def available_shells(self) -> list[str]:
        shells: list[str] = []
        for name, executable in (
            ("bash", "/bin/bash"),
            ("sh", "/bin/sh"),
            ("zsh", "/bin/zsh"),
            ("fish", "fish"),
            ("pwsh", "pwsh"),
        ):
            if executable.startswith("/"):
                if Path(executable).is_file():
                    shells.append(name)
            elif shutil.which(executable):
                shells.append(name)
        return shells

    def run_shell(
        self,
        command: str,
        cwd: Path,
        timeout: float,
        shell: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        selected = shell or "bash"
        if selected == "bash":
            argv = ["/bin/bash", "-lc", command]
        elif selected == "sh":
            argv = ["/bin/sh", "-c", command]
        elif selected == "zsh":
            argv = ["/bin/zsh", "-lc", command]
        elif selected == "fish":
            argv = ["fish", "-lc", command]
        elif selected == "pwsh":
            argv = ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command]
        else:
            raise ValueError(f"Unsupported Linux shell: {selected}")

        return subprocess.run(
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
