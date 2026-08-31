# Brookings Institution (Brown Center on Education Policy)

**Status (2026-08-30):** Weekly scraping off; the published set is 23 selected entries. Brookings' index labels every Brown Center item either Research or Commentary, and the Research label covers reports, briefs, analysis posts and event commentary alike. No field separates them, so the source can't be filtered to research outputs mechanically. Revisit if a format signal turns up (a series or program field, or categories in the WP REST API).

## Discovery

- **Method:** Algolia search API
- **Primary endpoint:** Algolia index `prod_searchable_posts`
  - App ID: `XGC391W2WE`
  - Search API key: `52dcafdcc61d4c5885aeccd7d2e4d788`
  - Filter: `(post_type:article) AND (tax_ids.center_tax:24) AND (locale:en)`
- **Alternative:** WP REST API at `https://www.brookings.edu/wp-json/wp/v2/article?slug={slug}` (per-article enrichment only — no taxonomy filtering)
- **Pagination:** Algolia returns up to 1,000 results per query (200 hits/page × 5 pages). For the full 1,239, use date-range windowing.
- **Total items:** 1,239 Brown Center articles (as of 2026-06-04)
- **Items per request:** Up to 200

## Access

- **Rendering:** Individual pages are server-rendered HTML. Discovery is API-only (listing pages use client-side Algolia).
- **Playwright:** Not needed — Algolia API + WP REST API cover everything
- **robots.txt:** Permissive. Blocks query-parameter search URLs and ~180 specific attachment paths. No AI restrictions.
- **llms.txt:** Not found
- **Rate limits:** None observed on Algolia search key. Standard Algolia rate limits may apply.

## Scope

- **Coverage strategy:** Research-like content types only
- **Include types:** Research (1,007), Commentary (232)
- **Exclude types:** Op-ed (33), Podcast (29), Testimony (6)
- **Current indexed:** 858 (Brown Center) after the 2026-08-30 backfill (`scrape.py brookings --backfill`: two date-window Algolia passes around the 1,000-hit cap — 727 articles before 2019, 525 after — then one page fetch per kept item for its meta description; 1,007 requests, every page once, 5 s gaps). 836 inserted (`page-meta` teasers, 31-744 chars; Algolia body kept as `page_text`, URL verified by the fetch); 161 pages with no meta description are pending rows; 231 Commentary items are excluded `type_filtered:Commentary` rows with their Algolia metadata and body text, no page fetched (user decision 2026-08-30). `type_allow` keeps Research only. Re-check the window split if either side nears 1,000.
- **Estimated remaining:** ~1,216
- **Scoping note:** Only Brown Center on Education Policy articles (center_tax:24). Other Brookings centers are out of scope.

## Entry metadata

**From Algolia API:**

| Field | Available | Quality |
|---|---|---|
| Title | `post_title` | Full |
| URL | `permalink` | Full canonical URL |
| Date | `post_date_formatted` | Human-readable |
| Description | `content` (opening text) | Several sentences — usable |
| Content type | `content_type` array | Research, Commentary, etc. |
| Authors | `display_authors` | Name strings |
| Experts | `experts` | Brookings expert names |
| Primary topic | `primary_topic` | Single string |
| Topics | `taxonomies.topic_tax` | Array of topic strings |
| Center | `entities` | Program/center names |

**From WP REST API (per-article enrichment):**
- `yoast_head_json.description` — the best 1-2 sentence summary
- `yoast_head_json.og_description` — same quality
- Full ACF fields, taxonomy IDs

**Description approach:** Algolia `content` field gives opening text. For polished 1-2 sentence descriptions, fetch Yoast meta via `https://www.brookings.edu/wp-json/wp/v2/article?slug={slug}&_fields=yoast_head_json`.

## Scraping instructions

Config-driven: `python scripts/scrape.py brookings` (config in `brookings.json`, rewritten 2026-08-30). Two date-window Algolia passes (`api.windows`, split at 2019-01-01) cover the Brown Center around Algolia's 1,000-hit cap; `type_allow` keeps Research items and records Commentary as `type_filtered` rows; each kept item's page supplies its meta description (`detail_fetch`, `page-meta`) and the Algolia body is kept as `page_text`. `early_stop` is not declared, so every page up to the cap is scanned each run. Backfilled 2026-08-30 with `--backfill`. Run modes and the request audit: `sources/README.md`.

## Quirks

- Algolia has a hard 1,000-result limit per query. Date-range windowing is needed to retrieve all 1,239 articles.
- The Algolia search API key is embedded in the page's JavaScript — it's a read-only search key, not a secret.
- Sitemaps contain ALL ~54,000 Brookings articles across all centers. There is no Brown Center-specific sitemap. Do not use sitemaps for discovery.
- Topic/center filtering is only available via Algolia (tax_ids.center_tax:24). The WP REST API article endpoint has no taxonomy filter params.
- Top experts: Michael Hansen (119), Jon Valant (88), Katharine Meyer (39), Rachel Perera (35), Douglas Harris (28).
