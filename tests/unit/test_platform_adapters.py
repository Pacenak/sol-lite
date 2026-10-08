import platform

import pytest

from sol_lite.platform import get_platform_adapter
from sol_lite.platform.base import PlatformAdapter
from sol_lite.platform.linux import LinuxAdapter
from sol_lite.platform.macos import MacOSAdapter
from sol_lite.platform.windows import WindowsAdapter


@pytest.mark.parametrize(
    "adapter",
    [WindowsAdapter(), MacOSAdapter(), LinuxAdapter()],
)
def test_platform_adapters_implement_contract(adapter):
    assert isinstance(adapter, PlatformAdapter)
    assert adapter.name in {"windows", "macos", "linux"}
    assert isinstance(adapter.available_shells(), list)


def test_linux_adapter_is_selectable_on_linux(monkeypatch):
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    assert isinstance(get_platform_adapter(), LinuxAdapter)


def test_linux_adapter_rejects_unknown_shell(tmp_path):
    with pytest.raises(ValueError, match="Unsupported Linux shell"):
        LinuxAdapter().run_shell("printf test", tmp_path, 1, shell="not-a-shell")


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux execution test")
def test_linux_adapter_executes_bash(tmp_path):
    result = LinuxAdapter().run_shell("printf 'sol-linux-ok'", tmp_path, 5)
    assert result.returncode == 0
    assert result.stdout == "sol-linux-ok"
