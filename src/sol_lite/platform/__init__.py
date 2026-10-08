"""Platform adapter selection."""

from __future__ import annotations

import platform

from .base import PlatformAdapter
from .linux import LinuxAdapter
from .macos import MacOSAdapter
from .windows import WindowsAdapter


def get_platform_adapter() -> PlatformAdapter:
    system = platform.system()
    if system == "Windows":
        return WindowsAdapter()
    if system == "Darwin":
        return MacOSAdapter()
    if system == "Linux":
        return LinuxAdapter()
    raise RuntimeError(f"Unsupported operating system: {system}")


__all__ = [
    "LinuxAdapter",
    "MacOSAdapter",
    "PlatformAdapter",
    "WindowsAdapter",
    "get_platform_adapter",
]
