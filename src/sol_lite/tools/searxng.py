"""SearXNG web-search integration for agents."""
from __future__ import annotations

from urllib.parse import urlparse

import httpx

from ..permissions.scopes import NETWORK
from .base import ToolDefinition


def _base_url(ctx) -> str:
    config = ctx.search_config or {}
    value = str(config.get("url", "")).strip()
    if not value:
        raise RuntimeError("SearXNG is not configured. Set searxng.url or SOL_SEARXNG_URL.")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("SearXNG URL must be an absolute HTTP or HTTPS URL.")
    return value.rstrip("/")


def searxng_search(ctx, args):
    config = ctx.search_config or {}
    if not bool(config.get("enabled", False)):
        raise RuntimeError("SearXNG integration is disabled. Enable it in config/searxng.yaml or SOL_SEARXNG_ENABLED.")
    base_url = _base_url(ctx)
    query = str(args["query"]).strip()
    if not query:
        raise ValueError("Search query must not be empty.")
    limit = max(1, min(int(args.get("max_results", config.get("max_results", 8))), 20))
    categories = str(args.get("categories", config.get("categories", "general")))
    language = str(args.get("language", config.get("language", "en")))
    time_range = str(args.get("time_range", ""))
    safe_search = int(args.get("safesearch", config.get("safesearch", 1)))
    engines = str(args.get("engines", ""))
    timeout = float(config.get("timeout_seconds", 15))

    params = {
        "q": query, "format": "json", "categories": categories,
        "language": language, "safesearch": safe_search,
    }
    if time_range:
        params["time_range"] = time_range
    if engines:
        params["engines"] = engines

    ctx.permission_engine.check(
        NETWORK,
        operation="network.searxng_search",
        target=base_url,
        arguments=params,
        plan=f"Search the configured SearXNG instance for: {query}",
    )
    response = httpx.get(f"{base_url}/search", params=params, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    data = response.json()
    results = []
    for item in data.get("results", [])[:limit]:
        results.append({
            "title": str(item.get("title", "")),
            "url": str(item.get("url", "")),
            "content": str(item.get("content", "")),
            "engine": str(item.get("engine", "")),
            "category": str(item.get("category", "")),
            "publishedDate": item.get("publishedDate"),
            "score": item.get("score"),
        })
    return {
        "ok": True, "query": query, "number_of_results": len(results),
        "results": results,
        "answers": data.get("answers", []),
        "corrections": data.get("corrections", []),
        "suggestions": data.get("suggestions", []),
        "unresponsive_engines": data.get("unresponsive_engines", []),
    }


def searxng_tools():
    return [
        ToolDefinition(
            "searxng_search",
            "Search the configured private SearXNG instance and return structured web results. Network permission still applies.",
            {"type": "object", "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "minimum": 1, "maximum": 20},
                "categories": {"type": "string"},
                "language": {"type": "string"},
                "time_range": {"type": "string", "enum": ["", "day", "month", "year"]},
                "safesearch": {"type": "integer", "minimum": 0, "maximum": 2},
                "engines": {"type": "string"},
            }, "required": ["query"]},
            searxng_search,
        )
    ]
