"""Exact, expiring, identity-bound operation approvals."""
from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    approval_id: str
    operation: str
    target: str
    arguments: dict
    plan_hash: str
    created_at: str
    session_id: str | None = None
    agent_id: str | None = None
    capability: str | None = None
    risk: tuple[str, ...] = ()
    expires_at: str | None = None


class ApprovalManager:
    """Create and consume exact, single-use, identity-bound approvals.

    Approval consumption is a security transaction. Validation and removal
    therefore occur atomically so concurrent callers cannot both consume the
    same approval.
    """

    def __init__(self, default_ttl_seconds: int = 900):
        if default_ttl_seconds <= 0:
            raise ValueError("default_ttl_seconds must be positive")

        self.default_ttl_seconds = default_ttl_seconds
        self._requests: dict[str, ApprovalRequest] = {}
        self._session_grants: set[tuple[str, str, str | None]] = set()
        self._lock = RLock()

    @staticmethod
    def plan_hash(plan: str) -> str:
        return hashlib.sha256(plan.encode("utf-8")).hexdigest()

    @staticmethod
    def _canon(value):
        return json.loads(
            json.dumps(
                value,
                sort_keys=True,
                ensure_ascii=False,
            )
        )

    def request(
        self,
        operation,
        target,
        arguments,
        plan,
        *,
        session_id=None,
        agent_id=None,
        capability=None,
        risk=(),
        ttl_seconds=None,
    ):
        ttl = (
            self.default_ttl_seconds
            if ttl_seconds is None
            else ttl_seconds
        )

        if ttl <= 0:
            raise ValueError("ttl_seconds must be positive")

        now = datetime.now(UTC)
        expiry = now + timedelta(seconds=ttl)

        request = ApprovalRequest(
            approval_id=secrets.token_urlsafe(18),
            operation=operation,
            target=target,
            arguments=self._canon(arguments),
            plan_hash=self.plan_hash(plan),
            created_at=now.isoformat(),
            session_id=session_id,
            agent_id=agent_id,
            capability=capability,
            risk=tuple(str(x) for x in risk),
            expires_at=expiry.isoformat(),
        )

        with self._lock:
            self._requests[request.approval_id] = request

        return request

    def consume(
        self,
        approval_id,
        operation,
        target,
        arguments,
        plan,
        *,
        session_id=None,
        agent_id=None,
        capability=None,
        risk=(),
    ):
        with self._lock:
            request = self._requests.get(approval_id)

            if request is None:
                return False

            if (
                request.operation != operation
                or request.target != target
                or request.plan_hash != self.plan_hash(plan)
            ):
                return False

            if request.arguments != self._canon(arguments):
                return False

            if (
                request.session_id != session_id
                or request.agent_id != agent_id
                or request.capability != capability
            ):
                return False

            if request.risk != tuple(str(x) for x in risk):
                return False

            if (
                request.expires_at
                and datetime.now(UTC)
                >= datetime.fromisoformat(request.expires_at)
            ):
                del self._requests[approval_id]
                return False

            # Delete while still holding the lock. This is the atomic
            # single-use security boundary.
            del self._requests[approval_id]
            return True

    def grant_session(self, *, session_id, scope, agent_id=None):
        """Remember a scope for the rest of this session.

        Exact approvals stay single-use. A session grant covers later calls
        of the same scope for this session (and this agent, when set).
        """
        sid = str(session_id or "").strip()
        scope_name = str(scope or "").strip()
        if not sid or not scope_name:
            raise ValueError("session_id and scope are required")
        agent = str(agent_id).strip() if agent_id else None
        with self._lock:
            self._session_grants.add((sid, scope_name, agent))

    def session_allows(self, *, session_id, scope, agent_id=None) -> bool:
        sid = str(session_id or "").strip()
        scope_name = str(scope or "").strip()
        if not sid or not scope_name:
            return False
        agent = str(agent_id).strip() if agent_id else None
        with self._lock:
            if (sid, scope_name, None) in self._session_grants:
                return True
            if agent and (sid, scope_name, agent) in self._session_grants:
                return True
        return False

    def clear(self):
        with self._lock:
            self._requests.clear()
            self._session_grants.clear()