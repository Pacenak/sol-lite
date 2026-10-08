"""Configured network storage locations without embedding credentials."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True, slots=True)
class StorageLocation:
    id: str
    kind: str
    location: str
    read_only: bool = False
    enabled: bool = True

    def validate(self) -> None:
        if not self.id or not self.kind or not self.location:
            raise ValueError("Storage location requires id, kind, and location")
        parsed = urlsplit(self.location)
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("Storage locations must not contain embedded credentials")
        if self.kind == "local":
            Path(self.location).expanduser()


class StorageRegistry:
    def __init__(self, locations=()):
        self._locations: dict[str, StorageLocation] = {}
        for location in locations:
            self.register(location)

    def register(self, location: StorageLocation) -> None:
        location.validate()
        if location.id in self._locations:
            raise ValueError(f"Duplicate storage location: {location.id}")
        self._locations[location.id] = location

    def get(self, location_id: str) -> StorageLocation:
        return self._locations[location_id]

    def all(self) -> tuple[StorageLocation, ...]:
        return tuple(self._locations.values())
