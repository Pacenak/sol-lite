"""Small, fail-closed HTTP client for the optional SOL-Command bridge.

The instance key is used only in request headers and is never included in
results, logs, or model context. Command remains responsible for checking the
instance's current sector assignment on every request.
"""
from __future__ import annotations

import json
import secrets
import socket
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urlsplit

import httpx


@dataclass(frozen=True, slots=True)
class SolCommandConfig:
    base_url: str
    instance_id: str
    instance_key: str
    timeout_seconds: float = 12.0

    def __post_init__(self) -> None:
        url = self.base_url.rstrip("/")
        parsed = urlsplit(url)
        loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
            raise ValueError("SOL-Command URL must use HTTPS (HTTP is allowed only for loopback).")
        if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("SOL-Command URL must be a base URL without credentials, query or fragment.")
        if not self.instance_id.strip() or not self.instance_key.strip():
            raise ValueError("SOL-Command instance ID and key are required.")
        if not 0 < self.timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be between 0 and 60.")
        object.__setattr__(self, "base_url", url)


class SolCommandClient:
    """Client for the documented `/api/lite/v1` Command surface."""

    def __init__(self, config: SolCommandConfig, *, transport: httpx.BaseTransport | None = None):
        self.config = config
        self._transport = transport

    @staticmethod
    def pair(base_url: str, invite_code: str, *, name: str = "SOL-Lite",
             wait_seconds: int = 600) -> dict[str, Any]:
        """Register, await Command approval, claim once, and save in OS keyring."""
        config = SolCommandConfig(base_url, "pairing", "pairing")
        token, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        headers = {"Accept": "application/json"}
        try:
            with httpx.Client(timeout=15.0, follow_redirects=False) as client:
                response = client.post(f"{config.base_url}/api/hub/pair/register",
                    headers=headers,
                    json={"token": token, "claim_nonce": nonce, "invite_code": invite_code,
                          "name": name, "host_hint": socket.gethostname(),
                          "client_type": "sol-lite"})
                response.raise_for_status()
                deadline = time.monotonic() + max(30, min(int(wait_seconds), 1800))
                while time.monotonic() < deadline:
                    status = client.get(f"{config.base_url}/api/hub/pair/status",
                                        params={"token": token}, headers=headers)
                    status.raise_for_status()
                    state = status.json()
                    if state.get("state") == "rejected":
                        raise RuntimeError("SOL-Command rejected this pairing request.")
                    if state.get("state") == "approved":
                        claim = client.post(f"{config.base_url}/api/hub/pair/claim",
                            headers=headers,
                            json={"token": token, "claim_nonce": nonce,
                                  "client_type": "sol-lite", "sol_version": "sol-lite-api-1"})
                        claim.raise_for_status()
                        credentials = claim.json().get("credentials") or {}
                        if not credentials.get("instance_id") or not credentials.get("api_key"):
                            raise RuntimeError("SOL-Command returned incomplete pairing credentials.")
                        from ..credentials.manager import CredentialManager, KeyringBackend
                        stored = {"command_url": config.base_url,
                                  "instance_id": credentials["instance_id"],
                                  "api_key": credentials["api_key"]}
                        CredentialManager(KeyringBackend()).store(
                            CredentialManager(KeyringBackend()).reference("SOL-Lite", "sol-command"),
                            json.dumps(stored),
                        )
                        return {"ok": True, "instance_id": stored["instance_id"],
                                "sectors": credentials.get("sectors") or []}
                    time.sleep(3)
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(f"SOL-Command pairing returned HTTP {exc.response.status_code}.") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"SOL-Command pairing failed: {type(exc).__name__}.") from exc
        raise TimeoutError("Pairing is still awaiting Command administrator approval.")

    @staticmethod
    def disconnect() -> None:
        from ..credentials.manager import CredentialManager, KeyringBackend
        manager = CredentialManager(KeyringBackend())
        reference = manager.reference("SOL-Lite", "sol-command")
        try:
            manager.delete(reference)
        except Exception:
            pass

    def _request(self, method: str, path: str, *, params=None, json=None) -> dict[str, Any]:
        headers = {
            "X-Sol-Instance-Id": self.config.instance_id,
            "X-Sol-Instance-Key": self.config.instance_key,
            "Accept": "application/json",
        }
        try:
            with httpx.Client(timeout=self.config.timeout_seconds, transport=self._transport,
                              follow_redirects=False) as client:
                response = client.request(method, f"{self.config.base_url}{path}",
                                          headers=headers, params=params, json=json)
            response.raise_for_status()
            if len(response.content) > 10 * 1024 * 1024:
                raise RuntimeError("SOL-Command response exceeded the 10 MiB limit.")
            payload = response.json()
        except httpx.HTTPStatusError as exc:
            # Do not include response bodies; some upstream errors can contain
            # sensitive request details.
            raise RuntimeError(f"SOL-Command returned HTTP {exc.response.status_code}.") from exc
        except RuntimeError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(f"SOL-Command request failed: {type(exc).__name__}.") from exc
        if not isinstance(payload, dict):
            raise RuntimeError("SOL-Command returned an invalid response.")
        if payload.get("ok") is False:
            raise RuntimeError(str(payload.get("error") or "SOL-Command rejected the request."))
        return payload

    def status(self) -> dict[str, Any]:
        return self._request("GET", "/api/lite/v1/status")

    def sync_pack_bodies(self, known_hashes: dict[str, str] | None = None) -> dict[str, Any]:
        return self._request("POST", "/api/hub/sync/packs", json={
            "instance_id": self.config.instance_id,
            "api_key": self.config.instance_key,
            "known_hashes": known_hashes or {},
        })

    def list_memories(self, sector_id: str) -> dict[str, Any]:
        sector = quote(sector_id, safe="")
        return self._request("GET", f"/api/lite/v1/sectors/{sector}/memories")

    def search_rag(self, sector_id: str, query: str, limit: int = 10) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        sector = quote(sector_id, safe="")
        return self._request("GET", f"/api/lite/v1/sectors/{sector}/rag/search",
                             params={"q": query, "limit": limit})

    def propose_to_jarvis(self, *, sector_id: str, title: str, body: str,
                          domain: str = "skills") -> dict[str, Any]:
        """Submit a proposal; Command policy keeps it pending for review."""
        if not title.strip() or len(title) > 200 or not body.strip() or len(body) > 12000:
            raise ValueError("Jarvis proposal title/body are empty or exceed their size limits")
        if domain not in {"meal_plans", "fitness_plans", "skills", "memories", "home_pa", "code_fix"}:
            raise ValueError("Unsupported SOL Jarvis proposal domain")
        sector = quote(sector_id, safe="")
        return self._request("POST", f"/api/lite/v1/sectors/{sector}/jarvis/proposals",
                             json={"title": title, "body": body, "domain": domain})
