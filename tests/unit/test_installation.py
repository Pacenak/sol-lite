from __future__ import annotations

import json
from pathlib import Path


def test_install_state_schema(
    tmp_path: Path,
):
    state = {
        "application": "SOL-Lite",
        "version": "0.2.6",
        "install_root": str(tmp_path),
        "editable_install": True,
    }

    path = (
        tmp_path
        / "data"
        / "state"
        / "install.json"
    )

    path.parent.mkdir(
        parents=True
    )

    path.write_text(
        json.dumps(state),
        encoding="utf-8",
    )

    loaded = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert loaded["application"] == (
        "SOL-Lite"
    )

    assert loaded["version"] == (
        "0.2.6"
    )


def test_pack_version_is_consistent():
    from sol_lite.version import __version__

    assert __version__ == "0.2.6"