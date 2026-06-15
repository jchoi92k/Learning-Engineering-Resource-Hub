# Brookings Institution (Brown Center on Education Policy)

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
- **Current indexed:** 23
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

```
1. Query Algolia for Brown Center articles:
   POST https://XGC391W2WE-dsn.algolia.net/1/indexes/prod_searchable_posts/query
   Headers:
     x-algolia-application-id: XGC391W2WE
     x-algolia-api-key: 52dcafdcc61d4c5885aeccd7d2e4d788
   Body:
     {
       "query": "",
       "hitsPerPage": 200,
       "page": 0,
       "filters": "(post_type:article) AND (tax_ids.center_tax:24) AND (locale:en)",
       "attributesToRetrieve": ["post_title","permalink","post_date_formatted","content","content_type","display_authors","primary_topic","taxonomies"]
     }

2. Algolia caps at 1,000 results. To get all 1,239:
   - First query: no date filter (gets 1,000 most relevant)
   - Then window by date: add filter AND (post_date < {earliest_date_from_first_batch})
   - Or use numericFilters on post_date (Unix timestamp)

3. Filter results: keep only content_type containing "Research" or "Commentary"

4. For each article, extract:
   - Title: post_title
   - URL: permalink
   - Date: post_date_formatted
   - Description: first 2 sentences of content field
   - Topics: taxonomies.topic_tax
   - Authors: display_authors
   - Type: map content_type → our taxonomy
     "Research" → report
     "Commentary" → blog-post

5. Optionally enrich descriptions via WP REST API:
   GET https://www.brookings.edu/wp-json/wp/v2/article?slug={slug}&_fields=yoast_head_json
   Use yoast_head_json.description as description.

6. Compare against existing entries in llms-full.txt
7. Stage new entries in docs/staging/brookings.txt
```

## Quirks

- Algolia has a hard 1,000-result limit per query. Date-range windowing is needed to retrieve all 1,239 articles.
- The Algolia search API key is embedded in the page's JavaScript — it's a read-only search key, not a secret.
- Sitemaps contain ALL ~54,000 Brookings articles across all centers. There is no Brown Center-specific sitemap. Do not use sitemaps for discovery.
- Topic/center filtering is only available via Algolia (tax_ids.center_tax:24). The WP REST API article endpoint has no taxonomy filter params.
- Top experts: Michael Hansen (119), Jon Valant (88), Katharine Meyer (39), Rachel Perera (35), Douglas Harris (28).
