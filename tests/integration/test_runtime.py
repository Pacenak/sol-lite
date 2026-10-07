from pathlib import Path

from sol_lite.bootstrap import bootstrap
from sol_lite.platform.windows import WindowsAdapter


def test_bootstrap_is_not_cwd_dependent(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sol_lite.bootstrap.get_platform_adapter", lambda: WindowsAdapter())
    runtime = bootstrap(root)
    assert runtime.application_name == "SOL-Lite"
    assert runtime.workspace_root == (root / "workspace").resolve()
