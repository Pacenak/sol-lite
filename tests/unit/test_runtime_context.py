from sol_lite.tools.base import ToolContext
from sol_lite.tools.context import runtime_get_context


class Perm:
    def check(self, scope):
        return None


class Platform:
    name = "test"
    def available_shells(self):
        return ["test-shell"]


def test_runtime_context_reports_authoritative_paths(tmp_path):
    ctx = ToolContext(tmp_path, Perm(), None, None, Platform(), session_id="s1", project_root=tmp_path)
    result = runtime_get_context(ctx, {})
    assert result["session_id"] == "s1"
    assert result["approved_workspace"] == str(tmp_path.resolve())
    assert result["project_root"] == str(tmp_path.resolve())
    assert "process_working_directory" in result
