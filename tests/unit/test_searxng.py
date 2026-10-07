from types import SimpleNamespace

import pytest

from sol_lite.tools.searxng import searxng_search


class Perm:
    def __init__(self):
        self.calls = []

    def check(self, *args, **kwargs):
        self.calls.append((args, kwargs))


def test_searxng_requires_config():
    ctx = SimpleNamespace(search_config={}, permission_engine=Perm())
    with pytest.raises(RuntimeError, match="disabled"):
        searxng_search(ctx, {"query": "test"})


def test_searxng_rejects_invalid_url():
    ctx = SimpleNamespace(search_config={"url": "not-a-url", "enabled": True}, permission_engine=Perm())
    with pytest.raises(ValueError, match="absolute HTTP or HTTPS"):
        searxng_search(ctx, {"query": "test"})


def test_searxng_requires_network_permission(monkeypatch):
    class Deny:
        def check(self, *args, **kwargs):
            raise RuntimeError("network gate")
    ctx = SimpleNamespace(search_config={"url": "http://127.0.0.1:8080", "enabled": True}, permission_engine=Deny())
    with pytest.raises(RuntimeError, match="network gate"):
        searxng_search(ctx, {"query": "test"})


def test_searxng_returns_structured_results(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [{"title": "Example", "url": "https://example.test", "content": "snippet", "engine": "test"}],
                "answers": [], "corrections": [], "suggestions": [], "unresponsive_engines": [],
            }

    def fake_get(url, **kwargs):
        assert url == "http://127.0.0.1:8080/search"
        assert kwargs["params"]["format"] == "json"
        return Response()

    monkeypatch.setattr("sol_lite.tools.searxng.httpx.get", fake_get)
    perm = Perm()
    ctx = SimpleNamespace(
        search_config={"url": "http://127.0.0.1:8080", "enabled": True, "max_results": 8},
        permission_engine=perm,
    )
    result = searxng_search(ctx, {"query": "SOL-Lite"})
    assert result["number_of_results"] == 1
    assert result["results"][0]["url"] == "https://example.test"
    assert perm.calls[0][0][0] == "network"
