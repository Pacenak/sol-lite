from __future__ import annotations

import ipaddress
import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


@dataclass(frozen=True, slots=True)
class DiscoveredModel:
    name: str
    capabilities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DiscoveredEndpoint:
    name: str
    provider: str
    endpoint: str
    locality: str
    reachable: bool
    trusted: bool
    models: tuple[DiscoveredModel, ...] = ()
    error: str | None = None


def _normalize_endpoint(endpoint: str) -> str:
    value = endpoint.strip().rstrip("/")
    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid model endpoint: {endpoint!r}")

    return value


def classify_locality(endpoint: str) -> str:
    parsed = urlparse(_normalize_endpoint(endpoint))
    host = (parsed.hostname or "").casefold()

    if host in {"localhost", "127.0.0.1", "::1"}:
        return "host"

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        # A hostname does not provide enough information to establish
        # that the endpoint is on the local/private network. Treat it
        # as external by default rather than trusting an unresolved
        # hostname as an internal network endpoint.
        return "external"

    if address.is_loopback:
        return "host"

    if address.is_private or address.is_link_local:
        return "network"

    return "external"


def _get_json(endpoint: str, path: str, timeout: float) -> dict:
    request = Request(endpoint + path, method="GET")

    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    if not isinstance(payload, dict):
        raise TypeError(
            f"Unexpected JSON response from {endpoint}{path}"
        )

    return payload


def discover_ollama(
    name: str,
    endpoint: str,
    *,
    timeout: float = 3.0,
    trusted: bool | None = None,
) -> DiscoveredEndpoint:
    normalized = _normalize_endpoint(endpoint)
    locality = classify_locality(normalized)

    effective_trust = (
        locality == "host"
        if trusted is None
        else bool(trusted)
    )

    try:
        _get_json(
            normalized,
            "/api/version",
            timeout,
        )

        tags = _get_json(
            normalized,
            "/api/tags",
            timeout,
        )

        models = tuple(
            DiscoveredModel(str(item["name"]))
            for item in tags.get("models", ())
            if isinstance(item, dict)
            and item.get("name")
        )

        return DiscoveredEndpoint(
            name,
            "ollama",
            normalized,
            locality,
            True,
            effective_trust,
            models,
        )

    except (
        HTTPError,
        URLError,
        OSError,
        TimeoutError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as exc:
        return DiscoveredEndpoint(
            name,
            "ollama",
            normalized,
            locality,
            False,
            effective_trust,
            error=str(exc),
        )


def discover_configured_endpoints(
    config: dict,
    *,
    timeout: float = 3.0,
) -> list[DiscoveredEndpoint]:
    provider = config.get("provider", {})
    endpoints = []

    if isinstance(provider, dict) and provider.get("endpoint"):
        endpoints.append(
            (
                str(
                    provider.get(
                        "name",
                        "ollama-local",
                    )
                ),
                str(
                    provider.get(
                        "type",
                        "ollama",
                    )
                ),
                str(provider["endpoint"]),
                bool(
                    provider.get(
                        "trusted",
                        False,
                    )
                ),
            )
        )

    for item in config.get("providers", ()):
        if (
            not isinstance(item, dict)
            or not item.get("endpoint")
        ):
            continue

        endpoints.append(
            (
                str(
                    item.get(
                        "name",
                        f"provider-{len(endpoints)}",
                    )
                ),
                str(
                    item.get(
                        "type",
                        "ollama",
                    )
                ),
                str(item["endpoint"]),
                bool(
                    item.get(
                        "trusted",
                        False,
                    )
                ),
            )
        )

    discovered = []

    for (
        name,
        provider_type,
        endpoint,
        trusted,
    ) in endpoints:
        if provider_type.casefold() == "ollama":
            discovered.append(
                discover_ollama(
                    name,
                    endpoint,
                    timeout=timeout,
                    trusted=trusted,
                )
            )

    return discovered