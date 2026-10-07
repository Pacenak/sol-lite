# SearXNG Integration

SOL-Lite can use a private SearXNG instance as its web-search backend. SearXNG exposes `/search` with `format=json` when JSON is enabled in the instance configuration. citeturn0search0

## 1. Configure SearXNG

In the SearXNG `settings.yml`, enable JSON in the search formats. The exact file can be supplied through `SEARXNG_SETTINGS_PATH`; otherwise SearXNG uses `/etc/searxng/settings.yml` when present. citeturn0search1turn0search5

Example override:

```yaml
use_default_settings: true

search:
  formats:
    - html
    - json

server:
  limiter: true
  image_proxy: true
```

Keep the instance private when it is intended for internal agents. Use your existing reverse proxy/authentication/network controls rather than exposing the endpoint unnecessarily.

## 2. Verify SearXNG

Replace the URL with the actual instance address:

```bash
curl "http://YOUR-SEARXNG/search?q=SOL-Lite&format=json"
```

The API supports query parameters including `q`, `categories`, `language`, `pageno`, `time_range`, `safesearch`, and `format`. citeturn0search0

## 3. Configure SOL-Lite

Edit `config/searxng.yaml`:

```yaml
searxng:
  url: "http://YOUR-SEARXNG"
  enabled: true
  timeout_seconds: 15
  max_results: 8
  categories: "general"
  language: "en"
  safesearch: 1
  engines: ""
```

Or set:

```text
SOL_SEARXNG_URL=http://YOUR-SEARXNG
SOL_SEARXNG_ENABLED=true
```

`SOL_SEARXNG_URL` overrides the YAML URL.

## 4. Agent use

All built-in agents receive the `searxng_search` tool. A call still passes through SOL-Lite's network permission gate. With the default policy, the first external search requires exact approval. This prevents a model from silently turning web access into unrestricted network access.

The result is structured data: title, URL, snippet/content, engine, category, publication date when available, score, answers, corrections, suggestions, and unresponsive engines.

## 5. Security boundary

SearXNG results are untrusted external content. They are evidence, not instructions. A page or search result cannot change SOL-Lite permissions, system instructions, approval requirements, or tool policy.

## 6. SearXNG instance tuning

SearXNG's `outgoing` configuration controls outbound engine requests, including request timeout, maximum timeout, connection pool size, HTTP/2, and optional proxy configuration. citeturn0search7

For agent workloads, start conservatively with a short request timeout and a modest result limit. Increase only when measured workloads require it.

## 7. Failure modes

- **403 from `/search`**: JSON is not enabled in SearXNG `search.formats`.
- **Connection refused**: wrong URL, port, container/network path, or service down.
- **Timeout**: SearXNG or one of its engines is slow; inspect SearXNG logs and outgoing timeout configuration.
- **No results**: inspect enabled engines/categories and query syntax.
- **Approval required**: expected under the default SOL-Lite network policy; approve the exact search operation.

## Official references

- SearXNG Search API: https://docs.searxng.org/dev/search_api.html
- SearXNG settings: https://docs.searxng.org/admin/settings/settings
- SearXNG outgoing settings: https://docs.searxng.org/admin/settings/settings_outgoing.html
