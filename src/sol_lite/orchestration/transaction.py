"""Plan/approval/execution/verification transaction boundary."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from ..core.exceptions import SOLLiteError


class TransactionExecutionError(SOLLiteError):
    """Raised when a transaction operation cannot be executed."""


class TransactionStage(StrEnum):
    DISCOVERY = "DISCOVERY"
    ANALYSIS = "ANALYSIS"
    PLAN = "PLAN"
    APPROVAL = "APPROVAL"
    EXECUTION = "EXECUTION"
    VERIFICATION = "VERIFICATION"
    REPORT = "REPORT"


@dataclass(frozen=True, slots=True)
class OperationPlan:
    operation: str
    target: str
    arguments: dict[str, Any]
    steps: tuple[str, ...]
    risk: tuple[str, ...] = ()
    plan_text: str = ""


@dataclass(slots=True)
class Transaction:
    transaction_id: str
    session_id: str
    plan: OperationPlan
    stage: TransactionStage = TransactionStage.DISCOVERY
    approval_id: str | None = None
    evidence: list[Any] = field(default_factory=list)
    verified: bool = False
    result: Any = None
    error: str | None = None


class TransactionEngine:
    def __init__(
        self,
        *,
        approve: Callable[[OperationPlan], str | None] | None = None,
    ):
        self.approve = approve

    @staticmethod
    def _execute_operation(
        operation: Callable[[dict[str, Any]], Any],
        arguments: dict[str, Any],
    ) -> Any:
        """Execute an operation and normalize callback failures.

        Transaction operations are intentionally generic callbacks. The
        transaction boundary therefore catches failures from the callback and
        converts them into the transaction-specific execution exception.
        """
        try:
            return operation(dict(arguments))
        except SOLLiteError:
            raise
        except Exception as exc:
            raise TransactionExecutionError(
                f"Transaction operation failed: {exc}"
            ) from exc

    def execute(
        self,
        tx: Transaction,
        operation: Callable[[dict[str, Any]], Any],
        verify: Callable[[Any], bool] | None = None,
    ) -> Transaction:
        tx.stage = TransactionStage.ANALYSIS
        tx.stage = TransactionStage.PLAN
        tx.stage = TransactionStage.APPROVAL

        if self.approve:
            tx.approval_id = self.approve(tx.plan)

        if self.approve and not tx.approval_id:
            tx.error = "Approval denied"
            return tx

        tx.stage = TransactionStage.EXECUTION

        try:
            tx.result = self._execute_operation(
                operation,
                tx.plan.arguments,
            )
        except SOLLiteError as exc:
            tx.error = str(exc)
            return tx

        tx.stage = TransactionStage.VERIFICATION
        tx.verified = (
            True
            if verify is None
            else bool(verify(tx.result))
        )

        if not tx.verified:
            tx.error = "Verification failed"

        tx.stage = TransactionStage.REPORT
        return tx