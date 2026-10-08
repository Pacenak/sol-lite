"""Task-scoped authorization for filesystem and storage resources."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from ..core.exceptions import PermissionDenied, SecurityError
from ..security.path_guard import is_within_directory


@dataclass(frozen=True, slots=True)
class AuthorizedResource:
    resource_id: str
    root: Path
    session_id: str
    operations: frozenset[str]
    source: str
    expires_at: datetime

    def permits(self, operation: str) -> bool:
        return operation in self.operations and datetime.now(UTC) < self.expires_at


class ResourceAuthorizer:
    """Authorizes explicit paths without expanding workspace authority."""

    def __init__(self, *, default_ttl_seconds: int = 3600):
        if default_ttl_seconds <= 0:
            raise ValueError("default_ttl_seconds must be positive")
        self.default_ttl_seconds = default_ttl_seconds
        self._resources: dict[str, AuthorizedResource] = {}

    def authorize_path(
        self,
        path: str | Path,
        *,
        session_id: str,
        operations: set[str] | frozenset[str],
        source: str = "user_explicit_path",
        ttl_seconds: int | None = None,
    ) -> AuthorizedResource:
        if not session_id:
            raise ValueError("session_id is required")
        resolved = Path(path).expanduser().resolve(strict=False)
        ops = frozenset(operations)
        if not ops:
            raise ValueError("At least one operation is required")
        ttl = self.default_ttl_seconds if ttl_seconds is None else ttl_seconds
        if ttl <= 0:
            raise ValueError("ttl_seconds must be positive")
        resource = AuthorizedResource(
            resource_id=uuid4().hex,
            root=resolved,
            session_id=session_id,
            operations=ops,
            source=source,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl),
        )
        self._resources[resource.resource_id] = resource
        return resource

    def resolve(
        self,
        resource_id: str,
        path: str | Path,
        *,
        session_id: str,
        operation: str,
    ) -> Path:
        resource = self._resources.get(resource_id)
        if resource is None:
            raise PermissionDenied("Authorized resource does not exist")
        if resource.session_id != session_id:
            raise PermissionDenied("Authorized resource belongs to another session")
        if not resource.permits(operation):
            raise PermissionDenied("Authorized resource does not permit this operation")
        candidate = Path(path).expanduser()
        candidate = candidate if candidate.is_absolute() else resource.root / candidate
        resolved = candidate.resolve(strict=False)
        if not is_within_directory(resolved, resource.root):
            raise SecurityError("Authorized path escapes the authorized resource root")
        return resolved

    def revoke(self, resource_id: str, *, session_id: str) -> None:
        resource = self._resources.get(resource_id)
        if resource is None:
            return
        if resource.session_id != session_id:
            raise PermissionDenied("Authorized resource belongs to another session")
        del self._resources[resource_id]

    def revoke_session(self, session_id: str) -> None:
        for resource_id, resource in list(self._resources.items()):
            if resource.session_id == session_id:
                del self._resources[resource_id]

    def list_session(self, session_id: str) -> tuple[AuthorizedResource, ...]:
        now = datetime.now(UTC)
        return tuple(
            resource
            for resource in self._resources.values()
            if resource.session_id == session_id and resource.expires_at > now
        )
