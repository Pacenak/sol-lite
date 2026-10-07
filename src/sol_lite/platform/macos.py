"""macOS shell adapter."""
import shutil
import subprocess
from pathlib import Path

from .base import PlatformAdapter


class MacOSAdapter(PlatformAdapter):
    name = "macos"

    def available_shells(self):
        shells = []
        for name, executable in (("zsh", "/bin/zsh"), ("bash", "/bin/bash"), ("pwsh", "pwsh")):
            if Path(executable).is_file() if executable.startswith("/") else shutil.which(executable):
                shells.append(name)
        return shells

    def run_shell(self, command: str, cwd: Path, timeout: float, shell: str | None = None):
        selected = shell or "zsh"
        if selected == "zsh":
            argv = ["/bin/zsh", "-lc", command]
        elif selected == "bash":
            argv = ["/bin/bash", "-lc", command]
        elif selected == "pwsh":
            argv = ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command]
        else:
            raise ValueError(f"Unsupported macOS shell: {selected}")
        return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout, check=False)
