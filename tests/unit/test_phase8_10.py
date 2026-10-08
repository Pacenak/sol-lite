from sol_lite.core.session import SessionManager, WorkspaceManager
from sol_lite.permissions.approvals import ApprovalManager
from sol_lite.storage.authorization import ResourceAuthorizer
from sol_lite.tools.base import ToolDefinition
from sol_lite.tools.registry import ToolRegistry

def test_tool_definition_keeps_old_constructor_and_exposes_capability():
    tool=ToolDefinition("x","test",{"type":"object"},lambda c,a:{"ok":True}); cap=tool.as_capability()
    assert cap.name=="x" and cap.parameters=={"type":"object"}

def test_registry_assigns_safe_default_metadata():
    reg=ToolRegistry(); reg.register(ToolDefinition("read_workspace_file","read",{},lambda c,a:None)); cap=reg.capabilities()["read_workspace_file"]
    assert "filesystem.read" in cap.permissions and not cap.mutability

def test_expiring_identity_bound_approval():
    manager=ApprovalManager(default_ttl_seconds=60); request=manager.request("write","x",{"v":1},"plan",session_id="s1",agent_id="a1",capability="write",risk=("MUTATING",))
    assert manager.consume(request.approval_id,"write","x",{"v":1},"plan",session_id="s1",agent_id="a1",capability="write",risk=("MUTATING",))
    assert not manager.consume(request.approval_id,"write","x",{"v":1},"plan",session_id="s1",agent_id="a1",capability="write",risk=("MUTATING",))

def test_explicit_resource_is_session_bound(tmp_path):
    root=tmp_path/"ws"; root.mkdir(); outside=tmp_path/"outside"; outside.mkdir(); wm=WorkspaceManager(tmp_path/"state.json"); ws=wm.register(root); sm=SessionManager(wm); s=sm.create("a",ws)
    auth=ResourceAuthorizer(default_ttl_seconds=60); resource=auth.authorize_path(outside,session_id=s.session_id,operations={"read"}); sm.bind_resource(s.session_id,resource.resource_id)
    assert resource.resource_id in sm.context(s.session_id)["authorized_resource_ids"]
    assert auth.resolve(resource.resource_id,".",session_id=s.session_id,operation="read")==outside.resolve()
