
import pytest

from sol_lite.core.exceptions import SecurityError
from sol_lite.security.path_guard import (
    is_within_directory,
    resolve_workspace_path,
)


def test_workspace_traversal_is_rejected(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(SecurityError):
        resolve_workspace_path(
            "../outside.txt",
            workspace,
        )


@pytest.mark.parametrize(
    "path",
    [
        "../outside.txt",
        "../../outside.txt",
        "sub/../../outside.txt",
        "/tmp/outside.txt",
    ],
)
def test_workspace_escape_paths_are_rejected(
    tmp_path,
    path,
):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    with pytest.raises(
        (SecurityError, ValueError)
    ):
        resolve_workspace_path(
            path,
            workspace,
        )


def test_valid_child_path_is_allowed(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = resolve_workspace_path(
        "src/example.py",
        workspace,
    )

    assert result == (
        workspace / "src" / "example.py"
    ).resolve()


def test_prefix_collision_is_not_containment(
    tmp_path,
):
    workspace = tmp_path / "workspace"
    collision = tmp_path / "workspace-other"

    workspace.mkdir()
    collision.mkdir()

    assert not is_within_directory(
        collision,
        workspace,
    )


def test_symlink_escape_is_rejected_when_supported(
    tmp_path,
):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"

    workspace.mkdir()
    outside.mkdir()

    link = workspace / "link"

    try:
        link.symlink_to(
            outside,
            target_is_directory=True,
        )
    except (
        OSError,
        NotImplementedError,
    ):
        pytest.skip(
            "Symlinks are unavailable on this platform."
        )

    with pytest.raises(SecurityError):
        resolve_workspace_path(
            "link/secret.txt",
            workspace,
        )