from pathlib import Path

import pytest

from sol_lite.repository.trust import RepositoryTrust


def test_config_root_allowlists_children(tmp_path):
    parent = tmp_path / "git"
    repo = parent / "proj"
    repo.mkdir(parents=True)
    trust = RepositoryTrust([parent], tmp_path / "trusted-repos.json")
    assert trust.is_allowlisted(repo) is True
    assert trust.is_trusted(repo) is False


def test_confirm_requires_allowlist(tmp_path):
    repo = tmp_path / "orphan"
    repo.mkdir()
    trust = RepositoryTrust([], tmp_path / "trusted-repos.json")
    with pytest.raises(PermissionError):
        trust.confirm(repo)


def test_confirm_with_allowlist_exact_for_first_run(tmp_path):
    repo = tmp_path / "host-repo"
    repo.mkdir()
    state = tmp_path / "trusted-repos.json"
    trust = RepositoryTrust([], state)
    trust.confirm(repo, allowlist_exact=True)
    assert trust.is_allowlisted(repo) is True
    assert trust.is_confirmed(repo) is True
    assert trust.is_trusted(repo) is True

    reloaded = RepositoryTrust([], state)
    assert reloaded.is_trusted(repo) is True


def test_confirm_under_config_root(tmp_path):
    parent = tmp_path / "git"
    repo = parent / "a"
    repo.mkdir(parents=True)
    trust = RepositoryTrust([parent], tmp_path / "trusted-repos.json")
    trust.confirm(repo)
    assert trust.is_trusted(repo) is True
    assert "allowlisted" in trust.explain_denial(tmp_path / "other").lower() or "not allowlisted" in trust.explain_denial(tmp_path / "other").lower()
