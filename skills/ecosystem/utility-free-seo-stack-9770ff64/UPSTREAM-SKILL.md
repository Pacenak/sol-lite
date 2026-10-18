---
name: free-seo-stack
allowed-tools: [Bash, WebFetch, WebSearch]
description: "Free alternatives to Semrush Ahrefs Ubersuggest paid SEO stack Lighthouse CrUX GSC Bing Yandex IndexNow rank audit backlinks security your scripts"
composes_with:
  - scraper-stack      # SERP queries and crawl use scraper-stack (not raw curl)
  - aeo-geo-100-score  # GEO/AEO scoring complements the technical SEO audit
  - contentos-pipeline # content optimization and on-page rewrite after audit findings
---

# Free SEO stack (Semrush / Ahrefs alternatives)

## When to use

- User mentions **Semrush**, **Ahrefs**, **paid SEO suite**, **no budget**, **free site audit**, **keyword tool without subscription**, **backlink checker free**, or wants a **repeatable technical + rank baseline** without vendor lock-in.
- Complements **`geo-audit`** (GEO/AEO visibility): this skill is **tooling + methodology**, not full GEO scoring.

## When not to use

- Client explicitly pays for Semrush/Ahrefs and wants workflow **inside** those products.
- Single trivial definition (“what is Domain Rating”) with no audit request.

---

## Technology radar (what actually strengthens the stack)

**Reality:** no free drop-in replaces Ahrefs-scale **backlink graph** or Semrush-scale **global keyword difficulty**. The stack below is **official APIs + owned measurement** first; paid APIs only as **explicit opt-in**.

| Tier | Sources | Role vs paid suites | your fit |
|------|---------|---------------------|----------|
| **S — Official, verified properties** | **GSC** (Search Analytics + **URL Inspection**), **CrUX**, **Lighthouse**, **PageSpeed/PSI API** | Performance + **your** queries/pages + index status | **Scripts** in `scripts/visual-verify/` |
| **S — Other engines (verify + API)** | [**Bing Webmaster**](https://learn.microsoft.com/en-us/bingwebmaster/) API (OAuth) | Queries, crawl issues, inbound links sample for Bing | **Future script** — same pattern as GSC: OAuth app, store tokens only in `your credentials config` |
| **S — RU market** | [**Yandex Webmaster API**](https://yandex.com/dev/webmaster/doc/en/) (OAuth) | Search queries / indexing for `.ru` properties | Same as Bing: official OAuth, no scrapers |
| **A — Publishing / crawl hints** | [**IndexNow**](https://www.indexnow.org/) | Push URLs to participating engines (Bing, etc.) | **Not** a rankings or backlink tool — **runbook**: host **public** key file on origin + `POST` submissions; key is **not** a vault secret (it is world-readable on the site) |
| **B — Opt-in paid data** | **DataForSEO**, **SerpAPI**, etc. | Volume, SERP snapshots at scale | **Out of “free stack”** — require **budget + ToS review**; keys only in `your credentials config`; never commit |
| **Red — High risk** | Gray **SERP scrapers**, “unofficial Google APIs”, shared cookie login services | May violate **search engine ToS** / account safety | **Do not** automate or recommend without **legal + security** sign-off; prefer official APIs |

### Integration map (your-repo)

| Capability | Tool | Status |
|------------|------|--------|
| Lab CWV | `lighthouse-mobile.mjs` | Shipped |
| Field CWV | `crux-field-metrics.mjs` | Shipped (GCP key) |
| GSC performance | `gsc-api-search-analytics.mjs` | Shipped (SA JWT) |
| GSC index status | `gsc-url-inspection-inspect.mjs` | Shipped (SA JWT; **quota-limited**) |
| Crawl-lite / headers | `free-seo-alt-signals.mjs` | Shipped |
| PSI UI (fragile) | `psi-pagespeed-stealth.mjs` | Shipped (optional) |
| Bundle | `phase0-external-evidence.mjs` | Shipped; set **`GSC_URL_INSPECTION=1`** to include URL Inspection |
| Bing / Yandex | REST + OAuth | **Documented here** — implement when a property is verified and tokens are available |

---

## Security and compliance (mandatory for agents)

1. **Secrets:** API keys, service account JSON paths, OAuth refresh tokens → **only** local **`your credentials config`** (gitignored). Never paste into client chats, tickets, or public Gists.
2. **Google Cloud keys:** Restrict **CrUX / PSI** keys to the specific APIs; avoid unrestricted browser keys in automation.
3. **GSC service account:** Principle of least privilege; property must **grant** the SA in Search Console UI — no “share my Google password” flows.
4. **URL Inspection:** Strict **daily quota** — use **`--max`** and small URL sets; never loop full sitemaps in CI without a product decision.
5. **IndexNow:** The key file is **published on the origin** by design — treat it like `robots.txt` visibility, **not** like an API secret in 1Password.
6. **Red tier:** Avoid recommending third-party **bulk Google SERP** scrapers as “Semrush replacement” — **ToS + account ban** risk; disclose if user insists.

---

## What paid suites usually provide (mental model)

| Bucket | Typical paid feature | Free / owned substitute |
|--------|----------------------|-------------------------|
| **Technical / CWV** | Site Audit, Core Web Vitals views | **Lighthouse** (lab), **CrUX API** (field p75), **PageSpeed** |
| **Search performance** | Organic keywords, landing pages | **GSC** `searchanalytics` |
| **Index state** | (partially) | **GSC URL Inspection** (quota) |
| **Rank tracking** | Daily positions for a keyword list | **SerpBear** (your Hermes), **Bing** / **Yandex** Webmaster |
| **Crawl / index** | On-page issues, duplicates | **GSC** coverage, **scripts** (`robots.txt`, sitemaps, `curl -I`), **`fetch` + HTML checks** |
| **Backlinks / authority** | Link index, competitor links | **No full free replacement** — **GSC Links** (limited), **Bing** link reports, **manual** checks |
| **Content / keyword research** | Volume, difficulty, SERP features | **GSC queries**, manual SERP / PAA, Trends (context only) |

---

## your automation (your-repo)

If the workspace is **`your-repo`** (or a clone with `scripts/visual-verify/`):

1. **Phase bundle** (artifacts under `.artifacts/hwai-phase0/`):
   ```bash
   node scripts/visual-verify/phase0-external-evidence.mjs
   ```
   Optional env: `SKIP_LIGHTHOUSE=1`, `SKIP_PSI_STEALTH=1`, **`GSC_URL_INSPECTION=1`** (adds URL Inspection for Phase0 URLs — **uses quota**).

2. **Pieces**
   - Lab LCP / CLS / INP (mobile): `node scripts/visual-verify/lighthouse-mobile.mjs`
   - Field CrUX (needs API key): `node scripts/visual-verify/crux-field-metrics.mjs`
   - GSC top queries + pages (SA JWT): `node scripts/visual-verify/gsc-api-search-analytics.mjs`  
     Resolves `https://example/` vs `sc-domain:example` via `sites.list` (`lib/gsc-site-resolve.mjs`).
   - **GSC URL Inspection** (index status, **low quota**):  
     `node scripts/visual-verify/gsc-url-inspection-inspect.mjs --url https://example.com/page`  
     or `--from-phase0` / `GSC_INSPECTION_URLS=...` — use **`--max`** to cap calls.
   - Free “crawl-lite”: `node scripts/visual-verify/free-seo-alt-signals.mjs`
   - Optional **pagespeed.web.dev** with stealth Playwright: `node scripts/visual-verify/psi-pagespeed-stealth.mjs`

3. **Credentials (local, never commit)**  
   `your credentials config`: GSC service account, optional `CHROME_UX_REPORT_API_KEY` / `GOOGLE_API_KEY`.  
   See **`claude/KNOWLEDGE_BASE.md`** (Phase 0.4–0.6 row).

4. **Rank / keyword gap**  
   Hermes **SerpBear** — KB **External Services → Hermes SerpBear**; not a Semrush clone, but covers **your keyword set** on a schedule.

---

## Agent workflow

1. Confirm goal: **technical baseline**, **GSC performance**, **index checks**, **rank tracking**, or **“like Semrush report”** (set expectations on backlinks/competitor depth).
2. If your repo available → run or instruct the scripts above; store **JSON + README** paths in `.artifacts/`.
3. If **no repo** → **manual checklist**: Lighthouse, GSC UI, CrUX in PSI, Bing + Yandex Webmaster (if relevant), `curl -I`, `robots.txt`, sitemap, IndexNow runbook if they own the origin.
4. Always note **residual gaps**: **full backlink index**, **global keyword difficulty at scale**, **historical competitor exports** — require paid data or primary research.
5. **Security:** follow **Security and compliance** above before suggesting any non-official API.

---

## Team copy (hwai-internal)

Canonical long-form mapping: **`the SEO alternatives doc`** in **`your-internal-docs`** (from seed).  
Install skill: `skills/imported/free-seo-stack/SKILL.md` → symlink to `~/.claude/skills/free-seo-stack` per `skills/README.md`.

---

## SSOT links (your-repo)

- `scripts/visual-verify/README.md`
- `the SEO audit plan` (Phase 0.4–0.6)
- `claude/KNOWLEDGE_BASE.md` — search “Phase 0.4–0.6”
