"""Execute one classified checklist row at a time."""
from __future__ import annotations

from .models import ProcedureDocument


class ProcedureSession:
    """Owns checklist progress. The model cannot mark a row done."""

    def __init__(self, document: ProcedureDocument):
        self.document = document
        self.stop_reason: str | None = None

    def status(self) -> dict:
        current = self._current()
        return {
            "source": self.document.source,
            "complete": self.document.complete,
            "stopped": self.stop_reason in {"failed", "blocked", "unverifiable"},
            "stop_reason": self.stop_reason,
            "current_step": None if current is None else current.step_id,
            "unparsed_sections": list(self.document.unparsed_sections),
            "steps": [
                {
                    "step_id": step.step_id,
                    "section": step.section,
                    "classification": step.classification,
                    "outcome": step.outcome,
                    "action": step.action,
                    "validate": step.validate,
                    "action_command": step.action_command,
                    "validate_command": step.validate_command,
                    "evidence": dict(step.evidence),
                }
                for step in self.document.steps
            ],
        }

    def advance(self, execute, approval_id=None) -> dict:
        """Run the current row, or stop when it cannot be verified."""
        if self.stop_reason in {"failed", "blocked", "unverifiable"}:
            return self.status()

        step = self._current()
        if step is None:
            return self.status()

        if step.classification in {"blocked", "unverifiable"}:
            self.stop_reason = step.classification
            return self.status()

        if step.classification == "human_gate":
            if not step.evidence.get("asked_turn"):
                step.evidence["asked_turn"] = int(step.evidence.pop("pending_turn", 0) or 1)
            step.outcome = "awaiting_user"
            self.stop_reason = "awaiting_user"
            status = self.status()
            status["ask"] = (
                f"Step {step.step_id} needs you before the next step: {step.action}"
            )
            return status

        if step.classification == "candidate":
            step.outcome = "candidate"
            self.stop_reason = "candidate"
            status = self.status()
            status["ask"] = f"Step {step.step_id} is a manual candidate and was not run."
            return status

        if step.classification == "needs_approval" and not approval_id:
            step.outcome = "approval_required"
            self.stop_reason = "approval_required"
            return self.status()

        if not step.validate_command:
            step.outcome = "unverifiable"
            self.stop_reason = "unverifiable"
            return self.status()

        evidence = {"approval_id": approval_id}
        if step.action_command:
            action = _run(execute, step.action_command)
            evidence["action"] = action
            if action["exit_code"] != 0:
                step.evidence = evidence
                step.outcome = "failed"
                self.stop_reason = "failed"
                return self.status()

        result = _run(execute, step.validate_command)
        evidence["validate"] = result
        step.evidence = evidence
        status = step.required_status
        passed = result["exit_code"] == 0 and (not status or status in result["stdout"])
        if not passed:
            step.outcome = "failed"
            self.stop_reason = "failed"
            return self.status()

        step.outcome = "verified"
        self.stop_reason = None
        return self.status()

    def acknowledge(self, step_id: str, user_text: str, turn_id: int) -> dict:
        step = self._current()
        status = self.status()
        if step is None or step.step_id != step_id:
            status["ok"] = False
            status["error"] = "That step is not the current row."
            return status
        if step.classification != "human_gate":
            status["ok"] = False
            status["error"] = "Only a human gate can be acknowledged."
            return status
        asked = int(step.evidence.get("asked_turn") or 0)
        if asked <= 0 or int(turn_id) <= asked:
            status["ok"] = False
            status["error"] = "The gate was asked this turn. Wait for the next reply."
            return status
        from ..studio.gate import explicit_completion
        if not explicit_completion(user_text):
            status["ok"] = False
            status["error"] = "The reply is not an explicit completion."
            return status
        step.outcome = "human_gate"
        self.stop_reason = None
        status = self.status()
        status["ok"] = True
        return status

    def snapshot_state(self, source: str) -> dict:
        return {
            "source": source,
            "stop_reason": self.stop_reason,
            "steps": [
                {
                    "step_id": step.step_id,
                    "outcome": step.outcome,
                    "evidence": dict(step.evidence),
                }
                for step in self.document.steps
            ],
        }

    def restore(self, payload: dict) -> None:
        saved = {
            item["step_id"]: item
            for item in payload.get("steps") or []
            if isinstance(item, dict) and item.get("step_id")
        }
        for step in self.document.steps:
            item = saved.get(step.step_id)
            if not item:
                continue
            outcome = str(item.get("outcome") or "")
            if outcome in {"verified", "human_gate", "awaiting_user", "failed", "candidate"}:
                step.outcome = outcome
                step.evidence = dict(item.get("evidence") or {})
        self.stop_reason = payload.get("stop_reason")

    def _current(self):
        for step in self.document.steps:
            if step.outcome in {"verified", "human_gate"}:
                continue
            return step
        return None


def _run(execute, command: str) -> dict:
    result = execute(command)
    if not isinstance(result, dict):
        raise TypeError("Procedure command did not return a result.")
    return {
        "command": command,
        "exit_code": int(result.get("exit_code", 1)),
        "stdout": str(result.get("stdout", "")),
        "stderr": str(result.get("stderr", "")),
    }
