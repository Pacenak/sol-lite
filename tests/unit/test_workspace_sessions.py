from sol_lite.core.session import SessionManager, WorkspaceManager


def test_workspace_and_session_are_isolated(tmp_path):
    manager = WorkspaceManager(tmp_path / "state.json")
    adir = tmp_path / "a"; adir.mkdir()
    a = manager.register(adir, "A")
    bdir = tmp_path / "b"; bdir.mkdir()
    b = manager.register(bdir, "B")
    sessions = SessionManager(manager)
    sa = sessions.create("sol_engineer", a)
    sb = sessions.create("sol_docs", b)
    assert sa.workspace_root != sb.workspace_root
    assert sessions.get(sa.session_id).agent_id == "sol_engineer"


def test_workspace_manager_reuses_same_real_path(tmp_path):
    manager = WorkspaceManager(tmp_path / "state.json")
    workspace_dir = tmp_path / "project"
    workspace_dir.mkdir()
    first = manager.register(workspace_dir)
    second = manager.register(workspace_dir / ".")
    assert first.workspace_id == second.workspace_id
    assert len(manager.list()) == 1
