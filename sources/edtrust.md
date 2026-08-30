# The Education Trust

## Discovery

- **Method:** WordPress REST API, post type `research-tools-and-i` (since 2026-08-30; the sitemap route below carries no descriptions)
- **Primary URL:** `https://edtrust.org/wp-json/wp/v2/research-tools-and-i?per_page=100&orderby=date&order=desc` (402 items in 5 pages on 2026-08-30)
- **Alternative:** `https://edtrust.org/research-tools-and-i-sitemap.xml` (582 `/rti/` URLs, no metadata) — discovery only
- **Pagination:** API `?page=N`; `per_page=100` is honoured and the run stops on a short page. Newest-first, so `early_stop` is declared.
- **Total items:** 402 in the API (2026-08-30); the `type-of-content` and `topic` taxonomies are resolved to names via `lookups`
- **Items per request:** 100

## Access

- **Rendering:** Individual resource pages are server-rendered HTML. No JS needed.
- **Playwright:** Not needed
- **robots.txt:** Permissive. Only `/wp-admin/`, `/trackback/`, `/xmlrpc.php`, `/feed/` blocked.
- **llms.txt:** Not found
- **Rate limits:** None observed. API hard-caps at 6 items/response regardless of `per_page` param.

## Scope

- **Coverage strategy:** Research-like content only (~318 items)
- **Include types:** Report (110), Brief (74), Guide (58), Compilation (32), Fact Sheet (25), Data Tool (11), Digital Report (4), Infographic (4)
- **Exclude types:** Blog Post (755), Press Releases (250), Public Statements (188), Public Letters (102), Public Comments (94), Op-Ed (22), Podcast (29), Video (39), State News (18), Public Testimony (23), Campaign (7)
- **Current indexed:** 362 after the 2026-08-30 backfill via the WordPress REST post type `research-tools-and-i` (`scrape.py edtrust --backfill`: 5 API pages of 100, 402 items, 10 requests, 5 s gaps): 331 inserted with the Yoast meta description (`page-meta`), article body kept as `page_text`, `type-of-content` and `topic` taxonomies resolved to names (`lookups`); 14 items without a description are pending rows; 26 (State News 18, Campaign 7, Press Releases 1) are excluded `type_filtered` rows. `type_allow` keeps Report, Brief, Guide, Compilation, Fact Sheet, Podcast, Video, Data Tool, Infographic, Digital Report. The June note that the API caps at 6 items per page did not hold: `per_page=100` is honoured. Five pre-2026 rows were re-pointed from `/resource/` to `/rti/` URLs.
- **Estimated remaining:** ~287
- **Type taxonomy:** `type-of-content` (19 terms). API endpoint: `https://edtrust.org/wp-json/wp/v2/type-of-content?per_page=100`

## Entry metadata

**From individual pages (server-rendered):**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full |
| URL | Yes | `/rti/{slug}/` |
| Date | Yes | Full date |
| Description | Yes | Opening paragraph — rich |
| Content type | Yes | In breadcrumb |
| Topics | Yes | Taxonomy terms |
| Authors | Yes | Byline |
| PDF link | Yes | `/wp-content/uploads/...` |

**From API:** Returns title, date, link, content (HTML), taxonomy IDs (need separate resolution), Yoast meta.

**Description approach:** Must fetch individual pages — no listing page exists (the `/research/` URL redirects to a single press release, and `/search/` is JS-only).

## Scraping instructions

Config-driven: `python scripts/scrape.py edtrust` (config in `edtrust.json`, rewritten 2026-08-30): WordPress REST post type `research-tools-and-i`, newest-first with `early_stop`; the Yoast meta description is the description (`page-meta`), the article body is kept as `page_text`, `lookups` resolve `type-of-content` and `topic` to names, and `type_allow` keeps Report, Brief, Guide, Compilation, Fact Sheet, Podcast, Video, Data Tool, Infographic and Digital Report (State News, Campaign and Press Releases become `type_filtered` rows). Backfilled 2026-08-30 with `--backfill`. Run modes and the request audit: `sources/README.md`.

## Quirks

- `/research/` is NOT a listing page — it resolves to the most recent news item tagged "research."
- `/search/` is entirely JS-driven (Algolia-like). No server-rendered results. Hash-based URL fragments for filters.
- WP REST API hard-caps responses at ~6 items regardless of `per_page`. Unreliable for full enumeration.
- The "1,903" resource count includes all post types across the site (blog, press-room, news, RTI). The RTI-specific sitemap has 582.
- Four regional subdomains exist (midwest, west, newyork) with their own sitemaps — currently out of scope.
