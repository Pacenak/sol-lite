from sol_lite.procedures import parse_procedure
from sol_lite.procedures.runner import ProcedureSession

PASS_FAIL = """
| Step | Action | Validate |
|------|--------|----------|
| A1 | `echo alpha` | `echo ok` |
| A2 | `echo beta` | `echo missing` |
| A3 | `echo gamma` | `echo ok` |
"""

BLOCKED = """
| Step | Action | Validate |
|------|--------|----------|
| P1 | `echo {{PLACEHOLDER}}` | `echo ok` |
| A1 | `echo alpha` | `echo ok` |
"""

PLANNED = """
| Step | Action | Validate |
|------|--------|----------|
| L1 | `echo later` [PLANNED] | `echo ok` |
| A1 | `echo alpha` | `echo ok` |
"""

HUMAN = """
| Step | Action | Validate |
|------|--------|----------|
| S1 | Create the admin password in Bitwarden `PLG Example` | login works |
| A1 | `echo alpha` | `echo ok` |
"""

APPROVAL = """
| Step | Action | Validate |
|------|--------|----------|
| I1 | `sudo bash scripts/install/plg-install-docker-official.sh` | `echo ok` |
"""

STATUS = """
| Step | Action | Validate |
|------|--------|----------|
| V1 | `echo status` | `echo HTTP/1.1 200` → 200 |
"""


def _session(text):
    return ProcedureSession(parse_procedure(text, source="fixture.md"))


def _executor(outputs):
    calls = []

    def execute(command):
        calls.append(command)
        exit_code, stdout = outputs.get(command, (0, "ok"))
        return {"exit_code": exit_code, "stdout": stdout, "stderr": ""}

    return calls, execute


def test_failing_validate_stops_the_next_step():
    calls, execute = _executor({"echo missing": (1, "missing")})
    session = _session(PASS_FAIL)

    first = session.advance(execute)
    assert first["steps"][0]["outcome"] == "verified"
    assert calls == ["echo alpha", "echo ok"]

    second = session.advance(execute)
    assert second["stop_reason"] == "failed"
    assert second["complete"] is False
    assert "echo gamma" not in calls
    assert session.advance(execute)["stop_reason"] == "failed"
    assert "echo gamma" not in calls


def test_placeholder_and_planned_rows_are_not_executed():
    calls, execute = _executor({})

    placeholder = _session(BLOCKED).advance(execute)
    assert placeholder["stop_reason"] == "blocked"
    assert calls == []

    planned = _session(PLANNED).advance(execute)
    assert planned["stop_reason"] == "blocked"
    assert calls == []


def test_bitwarden_row_is_a_human_gate_and_later_read_only_can_run():
    calls, execute = _executor({})
    session = _session(HUMAN)

    result = session.advance(execute)
    assert result["steps"][0]["classification"] == "human_gate"
    assert result["steps"][0]["outcome"] == "human_gate"
    assert calls == ["echo alpha", "echo ok"]
    assert result["complete"] is True


def test_needs_approval_does_not_run_without_an_approval_id():
    calls, execute = _executor({})
    session = _session(APPROVAL)

    denied = session.advance(execute)
    assert denied["stop_reason"] == "approval_required"
    assert calls == []

    approved = session.advance(execute, approval_id="approval-1")
    assert calls == [
        "sudo bash scripts/install/plg-install-docker-official.sh",
        "echo ok",
    ]
    assert approved["steps"][0]["outcome"] == "verified"
    assert approved["steps"][0]["evidence"]["approval_id"] == "approval-1"


def test_required_status_must_appear_in_validate_output():
    calls, execute = _executor({"echo HTTP/1.1 200": (0, "HTTP/1.1 500")})
    session = _session(STATUS)

    failed = session.advance(execute)
    assert failed["stop_reason"] == "failed"
    assert calls == ["echo status", "echo HTTP/1.1 200"]

    session = _session(STATUS)
    ok_calls, execute_ok = _executor({"echo HTTP/1.1 200": (0, "HTTP/1.1 200 OK")})
    assert session.advance(execute_ok)["complete"] is True
    assert ok_calls == ["echo status", "echo HTTP/1.1 200"]
