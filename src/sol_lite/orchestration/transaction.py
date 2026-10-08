"""Plan/approval/execution/verification transaction boundary."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Callable

class TransactionStage(StrEnum):
    DISCOVERY="DISCOVERY"; ANALYSIS="ANALYSIS"; PLAN="PLAN"; APPROVAL="APPROVAL"; EXECUTION="EXECUTION"; VERIFICATION="VERIFICATION"; REPORT="REPORT"

@dataclass(frozen=True, slots=True)
class OperationPlan:
    operation: str
    target: str
    arguments: dict[str,Any]
    steps: tuple[str,...]
    risk: tuple[str,...]=()
    plan_text: str=""

@dataclass(slots=True)
class Transaction:
    transaction_id: str
    session_id: str
    plan: OperationPlan
    stage: TransactionStage=TransactionStage.DISCOVERY
    approval_id: str|None=None
    evidence: list[Any]=field(default_factory=list)
    verified: bool=False
    result: Any=None
    error: str|None=None

class TransactionEngine:
    def __init__(self, *, approve: Callable[[OperationPlan],str|None]|None=None): self.approve=approve
    def execute(self, tx: Transaction, operation: Callable[[dict[str,Any]],Any], verify: Callable[[Any],bool]|None=None):
        tx.stage=TransactionStage.ANALYSIS
        tx.stage=TransactionStage.PLAN
        tx.stage=TransactionStage.APPROVAL
        if self.approve:
            tx.approval_id=self.approve(tx.plan)
        if self.approve and not tx.approval_id:
            tx.error="Approval denied"
            return tx
        tx.stage=TransactionStage.EXECUTION
        try: tx.result=operation(dict(tx.plan.arguments))
        except Exception as exc: tx.error=str(exc); return tx
        tx.stage=TransactionStage.VERIFICATION
        tx.verified=True if verify is None else bool(verify(tx.result))
        if not tx.verified: tx.error="Verification failed"
        tx.stage=TransactionStage.REPORT
        return tx
