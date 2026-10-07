"""Exact operation-bound approvals."""

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    approval_id: str
    operation: str
    target: str
    arguments: dict
    plan_hash: str
    created_at: str

class ApprovalManager:
    def __init__(self):
        self._requests = {}

    @staticmethod
    def plan_hash(plan: str) -> str:
        return hashlib.sha256(plan.encode("utf-8")).hexdigest()

    def request(self, operation, target, arguments, plan):
        r = ApprovalRequest(
            secrets.token_urlsafe(18), operation, target,
            json.loads(json.dumps(arguments, sort_keys=True)),
            self.plan_hash(plan), datetime.now(UTC).isoformat(),
        )
        self._requests[r.approval_id] = r
        return r

    def consume(self, approval_id, operation, target, arguments, plan):
        r = self._requests.get(approval_id)
        if r is None or r.operation != operation or r.target != target:
            return False
        if r.arguments != json.loads(json.dumps(arguments, sort_keys=True)):
            return False
        if r.plan_hash != self.plan_hash(plan):
            return False
        del self._requests[approval_id]
        return True

    def clear(self):
        self._requests.clear()
