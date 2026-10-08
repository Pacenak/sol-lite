"""Permission evaluation with execution-context-bound approvals."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from ..core.exceptions import ApprovalRequired, PermissionDenied
from .approvals import ApprovalManager
from .policy import PermissionPolicy

_EXECUTION: ContextVar[dict] = ContextVar("sol_lite_execution_context", default={})

@dataclass(slots=True)
class PermissionDecision:
    allowed: bool
    approval_required: bool
    reason: str

class PermissionEngine:
    def __init__(self, policy: PermissionPolicy, approvals: ApprovalManager):
        self.policy=policy; self.approvals=approvals
    @contextmanager
    def execution_context(self, *, session_id=None, agent_id=None, capability=None, risk=()):
        token=_EXECUTION.set({"session_id":session_id,"agent_id":agent_id,"capability":capability,"risk":tuple(str(x) for x in risk)})
        try: yield
        finally: _EXECUTION.reset(token)
    def check(self, scope, *, approval_id=None, operation="", target="", arguments=None, plan="", session_id=None, agent_id=None, capability=None, risk=()):
        ctx=_EXECUTION.get()
        session_id=ctx.get("session_id") if session_id is None else session_id
        agent_id=ctx.get("agent_id") if agent_id is None else agent_id
        capability=ctx.get("capability") if capability is None else capability
        risk=ctx.get("risk",()) if not risk else risk
        rule=self.policy.rule(*scope.split("."))
        if not rule.enabled: raise PermissionDenied(f"Permission scope disabled: {scope}")
        if not rule.approval_required: return PermissionDecision(True,False,"Allowed by policy.")
        capability=capability or operation
        if approval_id and self.approvals.consume(approval_id,operation,target,arguments or {},plan,session_id=session_id,agent_id=agent_id,capability=capability,risk=risk):
            return PermissionDecision(True,True,"Exact approval consumed.")
        request=self.approvals.request(operation,target,arguments or {},plan,session_id=session_id,agent_id=agent_id,capability=capability,risk=risk)
        raise ApprovalRequired(f"Approval required for {operation or scope} targeting {target}.",request=request)
