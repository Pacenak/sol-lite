from sol_lite.permissions.approvals import ApprovalManager


def test_exact_approval():
    m = ApprovalManager()
    r = m.request("write", "/a", {"content": "A"}, "plan A")
    assert m.consume(r.approval_id, "write", "/a", {"content": "A"}, "plan A")

def test_wrong_target_rejected():
    m = ApprovalManager()
    r = m.request("write", "/a", {"content": "A"}, "plan A")
    assert not m.consume(r.approval_id, "write", "/b", {"content": "A"}, "plan A")

def test_changed_plan_rejected():
    m = ApprovalManager()
    r = m.request("write", "/a", {"content": "A"}, "plan A")
    assert not m.consume(r.approval_id, "write", "/a", {"content": "A"}, "plan B")
