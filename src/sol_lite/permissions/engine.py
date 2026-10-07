"""Permission evaluation."""

from dataclasses import dataclass

from ..core.exceptions import ApprovalRequired, PermissionDenied
from .approvals import ApprovalManager
from .policy import PermissionPolicy


@dataclass(slots=True)
class PermissionDecision:
    allowed: bool
    approval_required: bool
    reason: str

class PermissionEngine:
    def __init__(self, policy: PermissionPolicy, approvals: ApprovalManager):
        self.policy = policy
        self.approvals = approvals

    def check(self, scope, *, approval_id=None, operation="", target="", arguments=None, plan=""):
        rule = self.policy.rule(*scope.split("."))
        if not rule.enabled:
            raise PermissionDenied(f"Permission scope disabled: {scope}")
        if not rule.approval_required:
            return PermissionDecision(True, False, "Allowed by policy.")
        if approval_id and self.approvals.consume(
            approval_id, operation, target, arguments or {}, plan
        ):
            return PermissionDecision(True, True, "Exact approval consumed.")
        request = self.approvals.request(operation, target, arguments or {}, plan)
        raise ApprovalRequired(
            f"Approval required for {operation or scope} targeting {target}.",
            request=request,
        )
