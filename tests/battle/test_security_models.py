from types import SimpleNamespace

from sol_lite.models.discovery import (
    classify_locality,
)
from sol_lite.models.routing import (
    ModelRouter,
)


def test_hostname_is_external():
    assert (
        classify_locality(
            "https://example.com"
        )
        == "external"
    )


def test_public_ip_is_external():
    assert (
        classify_locality(
            "https://8.8.8.8"
        )
        == "external"
    )


def test_private_ip_is_network():
    assert (
        classify_locality(
            "http://10.10.81.6:11434"
        )
        == "network"
    )


def test_loopback_ip_is_host():
    assert (
        classify_locality(
            "http://127.0.0.1:11434"
        )
        == "host"
    )


def test_localhost_is_host():
    assert (
        classify_locality(
            "http://localhost:11434"
        )
        == "host"
    )


def test_host_route_does_not_require_trusted_attribute():
    endpoint = SimpleNamespace(
        locality="host",
        capabilities=SimpleNamespace(
            chat=True,
        ),
    )

    provider = SimpleNamespace(
        endpoint=lambda: endpoint
    )

    profile = SimpleNamespace(
        name="default",
        model="qwen3-coder",
        provider=None,
        locality="auto",
        capabilities=("chat",),
    )

    router = ModelRouter(
        {"local": provider}
    )

    candidates = router.candidates(
        profile
    )

    assert len(candidates) == 1
    assert candidates[0].provider_name == "local"
    assert candidates[0].locality == "host"