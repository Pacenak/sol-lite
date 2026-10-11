from pathlib import Path

from sol_lite.core.runtime import Runtime, RuntimeConfig


def _config(**bridge):
    return RuntimeConfig(
        application={"name": "SOL-Lite", "version": "0.2.5"},
        runtime={},
        workspace={"root": "workspace"},
        data={"root": "data"},
        logging={},
        background={},
        macos={},
        nas={},
        bridge={"enabled": False, **bridge},
        windows={},
    )


def test_standalone_health_does_not_require_command(tmp_path: Path):
    result = Runtime(_config(), tmp_path).health_check()
    assert result.ok
    assert result.warnings == []


def test_bridge_listener_warning_keeps_pairing_separate(tmp_path: Path):
    result = Runtime(_config(enabled=True), tmp_path).health_check()
    assert result.ok
    assert result.warnings == [
        "The local bridge listener is enabled. SOL-Command pairing is separate; use 'sol-lite command-status'."
    ]
