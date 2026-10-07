from pathlib import Path

import pytest

from sol_lite.core.exceptions import SecurityError
from sol_lite.security.path_guard import is_within_directory, resolve_workspace_path


def test_commonpath_not_prefix():
    base = Path("/tmp/example")
    assert is_within_directory(base / "a.txt", base)
    assert not is_within_directory("/tmp/example-other/a.txt", base)

def test_parent_escape_rejected(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(SecurityError):
        resolve_workspace_path("../outside.txt", root)

def test_absolute_escape_rejected(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    with pytest.raises(SecurityError):
        resolve_workspace_path(tmp_path / "outside.txt", root)
