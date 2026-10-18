from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

from sol_lite.bootstrap import _sol_command_client
from sol_lite.integrations.sol_command import (
    SolCommandClient,
    SolCommandConfig,
    stage_synced_skills,
)
from sol_lite.tools.sol_command import _jarvis_propose, _memories, _status


def _client(handler):
    transport = httpx.MockTransport(handler)
    return SolCommandClient(
        SolCommandConfig("https://command.example", "inst-1", "key-1"),
        transport=transport,
    )


def test_config_requires_https_except_loopback():
    with pytest.raises(ValueError, match="HTTPS"):
        SolCommandConfig("http://command.example", "id", "key")
    SolCommandConfig("http://127.0.0.1:8787", "id", "key")


def test_status_uses_instance_headers_and_lite_route():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/lite/v1/status"
        assert request.headers["X-Sol-Instance-Id"] == "inst-1"
        assert request.headers["X-Sol-Instance-Key"] == "key-1"
        return httpx.Response(200, json={"ok": True, "instance_id": "inst-1", "sectors": ["home"]})

    result = _client(handler).status()
    assert result["sectors"] == ["home"]


def test_memories_and_rag_are_sector_scoped():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/memories"):
            assert request.url.path == "/api/lite/v1/sectors/home/memories"
            return httpx.Response(200, json={"ok": True, "items": [{"id": "m1"}]})
        assert request.url.path == "/api/lite/v1/sectors/home/rag/search"
        assert request.url.params["q"] == "notes"
        return httpx.Response(200, json={"ok": True, "items": []})

    client = _client(handler)
    assert client.list_memories("home")["items"][0]["id"] == "m1"
    assert client.search_rag("home", "notes")["items"] == []


def test_http_errors_do_not_include_response_bodies():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": "secret-key-in-body"})

    with pytest.raises(RuntimeError, match="HTTP 403") as exc:
        _client(handler).status()
    assert "secret-key-in-body" not in str(exc.value)


def test_pack_sync_uses_hub_body_contract():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/hub/sync/packs"
        body = request.read()
        assert b"inst-1" in body
        assert b"key-1" in body
        return httpx.Response(200, json={"ok": True, "packs_sync": {"sectors": {}}})

    assert _client(handler).sync_pack_bodies()["ok"] is True


def test_pair_claim_stores_keyring_secret(monkeypatch):
    stored = {}

    class Backend:
        def get(self, provider, key):
            raise KeyError(key)
        def set(self, provider, key, value):
            stored[(provider, key)] = value
        def delete(self, provider, key):
            stored.pop((provider, key), None)

    monkeypatch.setattr(
        "sol_lite.credentials.manager.KeyringBackend",
        lambda: Backend(),
    )
    calls = {"status": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/register"):
            payload = request.read()
            assert b'"client_type": "sol-lite"' in payload or b'"client_type":"sol-lite"' in payload
            return httpx.Response(200, json={"ok": True, "state": "pending"})
        if request.url.path.endswith("/status"):
            calls["status"] += 1
            return httpx.Response(200, json={"state": "approved"})
        assert request.url.path.endswith("/claim")
        return httpx.Response(200, json={
            "ok": True,
            "credentials": {"instance_id": "i-9", "api_key": "k-9", "sectors": ["ops"]},
        })

    result = SolCommandClient.pair(
        "https://command.example", "invite", wait_seconds=30,
        transport=httpx.MockTransport(handler), poll_interval=0.05,
    )
    assert result == {"ok": True, "instance_id": "i-9", "sectors": ["ops"]}
    assert "k-9" in stored[("SOL-Lite", "sol-command")]
    assert "api_key" not in str(result)


def test_stage_synced_skills_keeps_sector_names_with_spaces(tmp_path: Path):
    payload = {
        "packs_sync": {
            "sectors": {
                "Home PA": {
                    "body": {
                        "skills": [{
                            "name": "Briefing",
                            "description": "Daily briefing",
                            "steps": ["Collect notes"],
                        }]
                    }
                }
            }
        }
    }
    staged = stage_synced_skills(payload, tmp_path)
    assert len(staged) == 1
    skill = Path(staged[0]) / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "Home PA" in text
    assert "Daily briefing" in text
    assert skill.is_relative_to(tmp_path.resolve())


def test_command_tools_require_pairing_and_network_permission():
    class Deny:
        def check(self, *args, **kwargs):
            raise RuntimeError("network gate")

    ctx = SimpleNamespace(sol_command=None, permission_engine=Deny(), audit=SimpleNamespace(record=lambda *a, **k: None))
    with pytest.raises(RuntimeError, match="network gate"):
        _status(ctx, {})
    perm = SimpleNamespace(check=lambda *a, **k: None)
    ctx.permission_engine = perm
    with pytest.raises(RuntimeError, match="not configured"):
        _memories(ctx, {"sector_id": "home"})
    with pytest.raises(ValueError, match="required"):
        _jarvis_propose(ctx, {"sector_id": "", "title": "t", "body": "b"})


def test_disconnect_removes_the_saved_credential(monkeypatch):
    stored = {("SOL-Lite", "sol-command"): '{"api_key":"k-9"}'}

    class Backend:
        def get(self, provider, key):
            if (provider, key) not in stored:
                raise KeyError(key)
            return stored[(provider, key)]

        def set(self, provider, key, value):
            stored[(provider, key)] = value

        def delete(self, provider, key):
            stored.pop((provider, key), None)

    monkeypatch.setattr("sol_lite.credentials.manager.KeyringBackend", lambda: Backend())
    SolCommandClient.disconnect()
    assert stored == {}
    SolCommandClient.disconnect()


def test_sol_command_client_loader_uses_keyring_only(monkeypatch):
    monkeypatch.delenv("SOL_INSTANCE_ID", raising=False)
    monkeypatch.delenv("SOL_INSTANCE_KEY", raising=False)
    monkeypatch.delenv("SOL_COMMAND_URL", raising=False)

    class Backend:
        def get(self, provider, key):
            return '{"command_url":"https://command.example","instance_id":"i-1","api_key":"k-1"}'
        def set(self, provider, key, value):
            return None
        def delete(self, provider, key):
            return None

    monkeypatch.setattr("sol_lite.credentials.manager.KeyringBackend", lambda: Backend())
    client = _sol_command_client()
    assert client is not None
    assert client.config.instance_id == "i-1"

    monkeypatch.setenv("SOL_INSTANCE_KEY", "from-env")
    with pytest.raises(ValueError, match="keyring"):
        _sol_command_client()


def test_unavailable_os_keyring_does_not_break_optional_command(monkeypatch):
    from sol_lite.credentials.manager import KeyringBackend

    def denied(*args):
        raise OSError("Access denied")

    monkeypatch.delenv("SOL_INSTANCE_ID", raising=False)
    monkeypatch.delenv("SOL_INSTANCE_KEY", raising=False)
    monkeypatch.setattr(KeyringBackend, "_keyring", lambda self: SimpleNamespace(get_password=denied))
    assert _sol_command_client() is None
