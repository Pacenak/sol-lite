"""Remote node definitions."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class RemoteTransport(StrEnum):
    SSH = "ssh"
    POWERSHELL = "powershell"
    HTTP_API = "http_api"


@dataclass(frozen=True, slots=True)
class RemoteNode:
    id: str
    hostname: str
    platform: str
    transport: RemoteTransport
    port: int | None = None
    username: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
