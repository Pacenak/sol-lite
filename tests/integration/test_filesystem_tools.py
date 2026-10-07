import platform

import pytest

from sol_lite.core.exceptions import ApprovalRequired, SecurityError
from sol_lite.security.path_guard import resolve_workspace_path
from sol_lite.tools.filesystem import read_workspace_file, write_workspace_file

pytestmark = pytest.mark.skipif(
    platform.system() not in {"Windows", "Darwin"},
    reason="Platform integration tests are intended to run on Windows and macOS.",
)


def test_read(tool_context):
    result = read_workspace_file(tool_context, {"path": "src/example.py"})
    assert "answer = 42" in result["content"]


def test_write_requires_approval(tool_context):
    with pytest.raises(ApprovalRequired):
        write_workspace_file(tool_context, {
            "path": "src/new.py", "content": "x=1", "plan": "create new.py"
        })


def test_symlink_escape(tool_context, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = tool_context.workspace_root / "src" / "outside-link"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks unavailable.")
    with pytest.raises(SecurityError):
        resolve_workspace_path("src/outside-link", tool_context.workspace_root, must_exist=True)
