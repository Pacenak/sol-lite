"""Platform shell abstraction."""
from abc import ABC, abstractmethod
from pathlib import Path


class PlatformAdapter(ABC):
    name: str

    @abstractmethod
    def available_shells(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def run_shell(self, command: str, cwd: Path, timeout: float, shell: str | None = None):
        raise NotImplementedError
