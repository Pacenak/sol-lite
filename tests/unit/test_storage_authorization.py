from datetime import UTC, datetime, timedelta

import pytest

from sol_lite.core.exceptions import PermissionDenied, SecurityError
from sol_lite.storage import ResourceAuthorizer, StorageLocation, StorageRegistry


def test_explicit_path_is_session_bound_and_contained(tmp_path):
    auth = ResourceAuthorizer()
    resource = auth.authorize_path(tmp_path, session_id="s1", operations={"read", "write"})
    assert auth.resolve(resource.resource_id, "child/file.txt", session_id="s1", operation="read") == tmp_path / "child" / "file.txt"
    with pytest.raises(PermissionDenied):
        auth.resolve(resource.resource_id, "child/file.txt", session_id="s2", operation="read")
    with pytest.raises(SecurityError):
        auth.resolve(resource.resource_id, "../outside.txt", session_id="s1", operation="read")


def test_explicit_path_is_operation_scoped(tmp_path):
    auth = ResourceAuthorizer()
    resource = auth.authorize_path(tmp_path, session_id="s1", operations={"read"})
    with pytest.raises(PermissionDenied):
        auth.resolve(resource.resource_id, "file.txt", session_id="s1", operation="write")


def test_explicit_path_expires(tmp_path):
    auth = ResourceAuthorizer()
    resource = auth.authorize_path(tmp_path, session_id="s1", operations={"read"}, ttl_seconds=1)
    auth._resources[resource.resource_id] = resource.__class__(
        resource.resource_id, resource.root, resource.session_id, resource.operations,
        resource.source, datetime.now(UTC) - timedelta(seconds=1),
    )
    with pytest.raises(PermissionDenied):
        auth.resolve(resource.resource_id, ".", session_id="s1", operation="read")


def test_storage_rejects_embedded_credentials():
    with pytest.raises(ValueError):
        StorageLocation("nas", "smb", "smb://user:secret@example/nas").validate()


def test_storage_registry_rejects_duplicates():
    registry = StorageRegistry()
    registry.register(StorageLocation("nas", "smb", "smb://example/nas"))
    with pytest.raises(ValueError):
        registry.register(StorageLocation("nas", "smb", "smb://example/other"))
