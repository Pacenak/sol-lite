from dataclasses import replace

import pytest

from sol_lite.core.exceptions import (
    PermissionDenied,
    SecurityError,
)
from sol_lite.storage.authorization import (
    ResourceAuthorizer,
)


def test_resource_is_bound_to_session(tmp_path):
    root = tmp_path / "resource"
    root.mkdir()

    authorizer = ResourceAuthorizer()

    resource = authorizer.authorize_path(
        root,
        session_id="session-1",
        operations={"read"},
    )

    with pytest.raises(PermissionDenied):
        authorizer.resolve(
            resource.resource_id,
            ".",
            session_id="session-2",
            operation="read",
        )


def test_resource_is_bound_to_operation(tmp_path):
    root = tmp_path / "resource"
    root.mkdir()

    authorizer = ResourceAuthorizer()

    resource = authorizer.authorize_path(
        root,
        session_id="session-1",
        operations={"read"},
    )

    with pytest.raises(PermissionDenied):
        authorizer.resolve(
            resource.resource_id,
            ".",
            session_id="session-1",
            operation="write",
        )


def test_resource_traversal_is_rejected(tmp_path):
    root = tmp_path / "resource"
    outside = tmp_path / "outside"

    root.mkdir()
    outside.mkdir()

    authorizer = ResourceAuthorizer()

    resource = authorizer.authorize_path(
        root,
        session_id="session-1",
        operations={"read"},
    )

    with pytest.raises(SecurityError):
        authorizer.resolve(
            resource.resource_id,
            "../outside",
            session_id="session-1",
            operation="read",
        )


def test_revoked_resource_is_rejected(tmp_path):
    root = tmp_path / "resource"
    root.mkdir()

    authorizer = ResourceAuthorizer()

    resource = authorizer.authorize_path(
        root,
        session_id="session-1",
        operations={"read"},
    )

    authorizer.revoke(
        resource.resource_id,
        session_id="session-1",
    )

    with pytest.raises(PermissionDenied):
        authorizer.resolve(
            resource.resource_id,
            ".",
            session_id="session-1",
            operation="read",
        )


def test_expired_resource_is_rejected(tmp_path):
    root = tmp_path / "resource"
    root.mkdir()

    authorizer = ResourceAuthorizer()

    resource = authorizer.authorize_path(
        root,
        session_id="session-1",
        operations={"read"},
    )

    expired = replace(
        resource,
        expires_at=(
            resource.expires_at.replace(
                year=2000
            )
        ),
    )

    authorizer._resources[
        resource.resource_id
    ] = expired

    with pytest.raises(PermissionDenied):
        authorizer.resolve(
            resource.resource_id,
            ".",
            session_id="session-1",
            operation="read",
        )