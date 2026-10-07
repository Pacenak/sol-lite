"""Platform adapter selection."""

import platform

from .base import PlatformAdapter
from .macos import MacOSAdapter
from .windows import WindowsAdapter


def get_platform_adapter() -> PlatformAdapter:
    system = platform.system()
    if system == "Windows":
        return WindowsAdapter()
    if system == "Darwin":
        return MacOSAdapter()
    raise RuntimeError(f"Unsupported operating system: {system}")

__all__ = [
    "MacOSAdapter",
    "PlatformAdapter",
    "WindowsAdapter",
    "get_platform_adapter",
]
