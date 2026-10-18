import runpy
from pathlib import Path

import pytest
import yaml


def installer(tmp_path):
    module = runpy.run_path(str(Path(__file__).resolve().parents[2] / "scripts/install-rick-prime.py"))
    function = module["install"]
    function.__globals__["CONFIG"] = tmp_path / "agents.yaml"
    return function, module["ENTRY"], tmp_path / "agents.yaml"


def test_existing_description_is_preserved(tmp_path):
    install, entry, config = installer(tmp_path)
    original = yaml.safe_dump({"agents": {"rick_prime": dict(entry, description="Local prose")}})
    config.write_text(original, encoding="utf-8")
    assert "no change" in install()
    assert config.read_text(encoding="utf-8") == original


def test_conflicting_settings_remain_protected(tmp_path):
    install, entry, config = installer(tmp_path)
    original = yaml.safe_dump({"agents": {"rick_prime": dict(entry, enabled=False)}})
    config.write_text(original, encoding="utf-8")
    with pytest.raises(ValueError, match="different settings"):
        install()
    assert config.read_text(encoding="utf-8") == original


def test_fresh_install_is_repeatable(tmp_path):
    install, entry, config = installer(tmp_path)
    config.write_text("agents:\n  other: {enabled: true}\n", encoding="utf-8")
    install()
    assert yaml.safe_load(config.read_text())["agents"]["rick_prime"] == entry
    assert "no change" in install()
    assert config.with_suffix(".yaml.pre-rick-prime.bak").exists()
