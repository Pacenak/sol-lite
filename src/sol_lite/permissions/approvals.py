"""Exact, expiring, identity-bound operation approvals."""
from __future__ import annotations
import hashlib,json,secrets
from dataclasses import dataclass
from datetime import UTC,datetime,timedelta

@dataclass(frozen=True,slots=True)
class ApprovalRequest:
    approval_id:str; operation:str; target:str; arguments:dict; plan_hash:str; created_at:str
    session_id:str|None=None; agent_id:str|None=None; capability:str|None=None
    risk:tuple[str,...]=(); expires_at:str|None=None

class ApprovalManager:
    def __init__(self, default_ttl_seconds:int=900):
        if default_ttl_seconds<=0: raise ValueError("default_ttl_seconds must be positive")
        self.default_ttl_seconds=default_ttl_seconds; self._requests={}
    @staticmethod
    def plan_hash(plan:str)->str: return hashlib.sha256(plan.encode("utf-8")).hexdigest()
    @staticmethod
    def _canon(value): return json.loads(json.dumps(value,sort_keys=True,ensure_ascii=False))
    def request(self,operation,target,arguments,plan,*,session_id=None,agent_id=None,capability=None,risk=(),ttl_seconds=None):
        now=datetime.now(UTC); expiry=now+timedelta(seconds=ttl_seconds or self.default_ttl_seconds)
        request=ApprovalRequest(secrets.token_urlsafe(18),operation,target,self._canon(arguments),self.plan_hash(plan),now.isoformat(),session_id,agent_id,capability,tuple(str(x) for x in risk),expiry.isoformat())
        self._requests[request.approval_id]=request; return request
    def consume(self,approval_id,operation,target,arguments,plan,*,session_id=None,agent_id=None,capability=None,risk=()):
        request=self._requests.get(approval_id)
        if request is None or request.operation!=operation or request.target!=target or request.plan_hash!=self.plan_hash(plan): return False
        if request.arguments!=self._canon(arguments): return False
        if request.session_id!=session_id or request.agent_id!=agent_id or request.capability!=capability: return False
        if request.risk!=tuple(str(x) for x in risk): return False
        if request.expires_at and datetime.now(UTC)>=datetime.fromisoformat(request.expires_at):
            del self._requests[approval_id]; return False
        del self._requests[approval_id]; return True
    def clear(self): self._requests.clear()
