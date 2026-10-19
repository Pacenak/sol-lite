"""Small, fail-closed HTTP client for the optional SOL-Command bridge.

The instance key is used only in request headers and is never included in
results, logs, or model context. Command remains responsible for checking the
instance's current sector assignment on every request.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from collections.abc import Callable
from urllib.parse import quote, urlsplit

import httpx
import yaml


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
        if parsed.path:
            raise ValueError("Use the SOL-Command base URL only, without /setup, /command/pair or /api paths.")
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
             wait_seconds: int = 600, transport: httpx.BaseTransport | None = None,
             poll_interval: float = 3.0,
             progress: Callable[[str], None] | None = None) -> dict[str, Any]:
        """Register, await Command approval, claim once, and save in OS keyring."""
        config = SolCommandConfig(base_url, "pairing", "pairing")
        invite_code = invite_code.strip()
        if not invite_code:
            raise ValueError("A fresh Command pairing invite is required.")
        report = progress or (lambda message: None)
        from ..credentials.manager import KeyringBackend
        backend = KeyringBackend()
        probe_key = "pairing-check-" + secrets.token_hex(8)
        probe_value = secrets.token_urlsafe(24)
        try:
            backend.set("SOL-Lite", probe_key, probe_value)
            if backend.get("SOL-Lite", probe_key) != probe_value:
                raise RuntimeError("Credential storage round-trip failed.")
        except Exception:
            raise RuntimeError("OS keyring check failed before registration. Repair credential storage and retry; no invite was submitted.") from None
        finally:
            try:
                backend.delete("SOL-Lite", probe_key)
            except Exception:
                pass
        token, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        headers = {"Accept": "application/json"}
        stage = "registration"
        report("Registering SOL-Lite with SOL-Command...")
        try:
            with httpx.Client(timeout=15.0, follow_redirects=False, transport=transport) as client:
                response = client.post(f"{config.base_url}/api/hub/pair/register",
                    headers=headers,
                    json={"token": token, "claim_nonce": nonce, "invite_code": invite_code,
                          "name": name, "host_hint": socket.gethostname(),
                          "client_type": "sol-lite"})
                response.raise_for_status()
                registration = response.json()
                if not isinstance(registration, dict) or registration.get("state") != "pending":
                    raise RuntimeError("SOL-Command registration did not return a pending request.")
                report("Registered as SOL-Lite. Waiting for an administrator to approve this client on Command's Pair page (up to 10 minutes).")
                stage = "approval polling"
                deadline = time.monotonic() + max(30, min(int(wait_seconds), 1800))
                while time.monotonic() < deadline:
                    status = client.get(f"{config.base_url}/api/hub/pair/status",
                                        params={"token": token}, headers=headers)
                    status.raise_for_status()
                    state = status.json()
                    if not isinstance(state, dict):
                        raise RuntimeError("SOL-Command approval polling returned an invalid response.")
                    if state.get("state") in {"unknown", "expired", "claimed"}:
                        raise RuntimeError("Pairing request expired, was removed/rejected, or was already claimed. Check Command and request a fresh invite.")
                    if state.get("state") == "rejected":
                        raise RuntimeError("SOL-Command rejected this pairing request.")
                    if state.get("state") == "approved":
                        stage = "credential claim"
                        report("Approved. Claiming SOL-Lite credentials...")
                        claim = client.post(f"{config.base_url}/api/hub/pair/claim",
                            headers=headers,
                            json={"token": token, "claim_nonce": nonce,
                                  "client_type": "sol-lite", "sol_version": "sol-lite-api-1"})
                        claim.raise_for_status()
                        credentials = claim.json().get("credentials") or {}
                        if not credentials.get("instance_id") or not credentials.get("api_key"):
                            raise RuntimeError("SOL-Command returned incomplete pairing credentials.")
                        stored = {"command_url": config.base_url,
                                  "instance_id": credentials["instance_id"],
                                  "api_key": credentials["api_key"]}
                        try:
                            backend.set("SOL-Lite", "sol-command", json.dumps(stored))
                        except Exception:
                            raise RuntimeError("Credentials were claimed but could not be saved in the OS keyring. Ask the administrator to retire this instance, repair the keyring, then pair with a fresh invite.") from None
                        report("Credentials saved in the OS keyring. Run sol-lite command-status to verify live access.")
                        return {"ok": True, "instance_id": stored["instance_id"],
                                "sectors": credentials.get("sectors") or []}
                    time.sleep(max(0.05, min(float(poll_interval), 15.0)))
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            hint = {
                400: "Check that the invite is fresh, unused, and not reserved by another attempt.",
                401: "Check Command mode and proxy routing; this machine endpoint must not require a browser login.",
                403: "Check Command access policy and proxy routing.",
                404: "Check the Command base URL and deployed pairing API routes.",
                409: "Check the approved client type is sol-lite and both deployments support Lite pairing.",
                410: "The one-time claim is unavailable; ask the administrator to retire the stale instance and issue a new invite.",
            }.get(code, "Check Command and proxy logs for this stage.")
            if 300 <= code < 400:
                hint = "Use the canonical HTTPS base URL; pairing does not follow redirects."
            raise RuntimeError(f"SOL-Command {stage} returned HTTP {code}. {hint}") from None
        except httpx.HTTPError as exc:
            raise RuntimeError(f"SOL-Command {stage} failed ({type(exc).__name__}). Check DNS, connectivity and TLS certificate trust.") from None
        except (ValueError, AttributeError):
            raise RuntimeError(f"SOL-Command {stage} returned invalid JSON. Check that the URL reaches the Command API, not an HTML login page.") from None
        raise TimeoutError("Pairing is still awaiting Command administrator approval.")

    @staticmethod
    def disconnect() -> None:
        from ..credentials.manager import CredentialManager, KeyringBackend
        manager = CredentialManager(KeyringBackend())
        reference = manager.reference("SOL-Lite", "sol-command")
        try:
            manager.delete(reference)
        except Exception as exc:
            if not isinstance(exc, KeyError) and "not found" not in str(exc).casefold():
                raise

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
            raise RuntimeError("SOL-Command returned an invalid response.")  # noqa: TRY004
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


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9._-]+", "-", str(value).lower()).strip("-._")
    if not slug or ".." in slug:
        return ""
    return slug


def stage_synced_skills(payload: dict[str, Any], pending_root: Path) -> list[str]:
    """Write Command pack skills into a pending-review tree. Never activates them."""
    root = pending_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    discovered: list[str] = []
    sectors = (payload.get("packs_sync") or {}).get("sectors") or {}
    if not isinstance(sectors, dict):
        return discovered
    for sector_id, entry in sectors.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("body"), dict):
            continue
        sector_slug = _safe_slug(str(sector_id))
        if not sector_slug:
            continue
        for skill in entry["body"].get("skills") or []:
            if not isinstance(skill, dict):
                continue
            name = str(skill.get("name") or skill.get("title") or "").strip()
            slug = _safe_slug(name)
            if not slug:
                continue
            description = str(skill.get("description") or skill.get("summary") or name).strip()
            if len(description) > 2000:
                description = description[:2000]
            steps = skill.get("procedure") or skill.get("steps") or []
            body_lines = [f"# {name}", "", description, ""]
            if isinstance(steps, list):
                body_lines.extend(f"{idx}. {str(step)[:4000]}" for idx, step in enumerate(steps[:200], 1))
            elif isinstance(steps, str):
                body_lines.append(steps)
            refs = skill.get("references")
            if isinstance(refs, list) and refs:
                body_lines.extend(["", "## References", ""])
                body_lines.extend(f"- {ref!s}" for ref in refs)
            frontmatter = yaml.safe_dump(
                {"name": slug, "description": description, "source": "sol-command",
                 "sector": str(sector_id)},
                sort_keys=False,
            ).strip()
            content = f"---\n{frontmatter}\n---\n\n" + "\n".join(body_lines)
            version = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
            destination = root / sector_slug / slug / version
            if not destination.resolve().is_relative_to(root):
                continue
            destination.mkdir(parents=True, exist_ok=True)
            skill_file = destination / "SKILL.md"
            if not skill_file.exists():
                skill_file.write_text(content, encoding="utf-8")
            discovered.append(str(destination))
    return discovered
