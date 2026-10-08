from pathlib import Path
from sol_lite.guides import Guide, GuideResolver, build_plan
from sol_lite.orchestration import OperationPlan, Transaction, TransactionEngine

def test_guide_resolver(tmp_path: Path):
    root=tmp_path/"guides"; root.mkdir()
    (root/"linux.json").write_text('{"identity":"ubuntu-service","platform":"linux","target_type":"service","procedure":["inspect","apply"],"verification":["status"]}',encoding="utf-8")
    r=GuideResolver([root]); r.load(); matches=r.resolve("ubuntu service",platform="linux",target_type="service")
    assert matches and matches[0].guide.identity=="ubuntu-service"
    assert build_plan(matches[0].guide).verification==("status",)

def test_transaction_requires_approval():
    tx=Transaction("tx","session",OperationPlan("write","x",{"v":1},("write",)))
    out=TransactionEngine(approve=lambda plan: None).execute(tx,lambda a:{"ok":True})
    assert out.error=="Approval denied" and out.stage.value=="APPROVAL"

def test_transaction_verifies():
    tx=Transaction("tx","session",OperationPlan("write","x",{"v":1},("write",)))
    out=TransactionEngine(approve=lambda plan:"approval").execute(tx,lambda a:{"ok":True},lambda result:result["ok"])
    assert out.verified and out.stage.value=="REPORT"
