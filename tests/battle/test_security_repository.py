import pytest

from sol_lite.tools.repository import (
    _reject_embedded_credentials,
    _safe_remote,
)


@pytest.mark.parametrize(
    "url",
    [
        "https://user:password@example.com/repo.git",
        "https://user@example.com/repo.git",
        "http://user:password@example.com/repo.git",
    ],
)
def test_embedded_credentials_are_rejected(url):
    with pytest.raises(ValueError):
        _reject_embedded_credentials(url)


@pytest.mark.parametrize(
    ("remote", "expected"),
    [
        (
            "https://user:password@example.com/repo.git",
            "https://example.com/repo.git",
        ),
        (
            "https://example.com/repo.git?token=secret#fragment",
            "https://example.com/repo.git",
        ),
        (
            "git@example.com:repo.git",
            "example.com:repo.git",
        ),
    ],
)
def test_safe_remote_removes_sensitive_components(
    remote,
    expected,
):
    assert _safe_remote(remote) == expected


def test_safe_remote_preserves_safe_https_url():
    remote = (
        "https://example.com/"
        "owner/repository.git"
    )

    assert _safe_remote(remote) == remote