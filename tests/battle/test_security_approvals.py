from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from sol_lite.permissions.approvals import (
    ApprovalManager,
)


def _request(manager):
    return manager.request(
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def _consume(manager, approval_id):
    return manager.consume(
        approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def test_approval_is_single_use():
    manager = ApprovalManager()

    request = _request(manager)

    assert _consume(
        manager,
        request.approval_id,
    )

    assert not _consume(
        manager,
        request.approval_id,
    )


def test_changed_arguments_are_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "different",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def test_changed_target_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/other-workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def test_changed_plan_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "different plan",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def test_session_mismatch_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-2",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def test_agent_mismatch_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-2",
        capability="repository_commit",
        risk=("MUTATING",),
    )


def test_capability_mismatch_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_push",
        risk=("MUTATING",),
    )


def test_risk_mismatch_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    assert not manager.consume(
        request.approval_id,
        "repository_commit",
        "/workspace",
        {
            "path": "/workspace",
            "message": "approved",
        },
        "commit approved",
        session_id="session-1",
        agent_id="agent-1",
        capability="repository_commit",
        risk=("MUTATING", "NETWORK"),
    )


def test_expired_approval_is_rejected():
    manager = ApprovalManager()

    request = _request(manager)

    expired = replace(
        request,
        expires_at=(
            "2000-01-01T00:00:00+00:00"
        ),
    )

    manager._requests[
        request.approval_id
    ] = expired

    assert not _consume(
        manager,
        request.approval_id,
    )


def test_concurrent_consumption_allows_exactly_one():
    manager = ApprovalManager()

    request = _request(manager)

    with ThreadPoolExecutor(
        max_workers=8
    ) as executor:
        results = list(
            executor.map(
                lambda _: _consume(
                    manager,
                    request.approval_id,
                ),
                range(8),
            )
        )

    assert sum(results) == 1