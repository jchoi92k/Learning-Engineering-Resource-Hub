# Campbell Collaboration

## Discovery

- **Method:** WordPress REST API with URL filter
- **Endpoint:** `https://www.campbellcollaboration.org/wp-json/wp/v2/review?per_page=100&_fields=id,slug,title,link,content`
- **Filter:** Education group page at `/education/reviews/` provides the allowlist (~52 slugs). API returns all 307 reviews; scrape.py's `url_filter` keeps only education matches.
- **Total:** 307 published reviews (X-WP-Total header), ~52 education. Sitemap has 458 URLs (includes protocols/withdrawn).
- **Platform:** WordPress (custom `review` post type)

## Access

- **robots.txt:** Standard WP — only `/wp-admin/` blocked. No AI bot restrictions.
- **llms.txt:** None (404).
- **Sitemap:** `wp-sitemap-posts-review-1.xml` has all 458 review URLs.
- **Authentication:** None required. Full-text systematic reviews are on Wiley (paywalled, HTTP 402) but Campbell's own plain-language summaries are freely accessible.

## Scope

Systematic reviews across 11 coordinating groups: Crime & Justice, Education, International Development, Social Welfare, Methods, Knowledge Translation, Disability, Business & Management, Ageing, Children & Young People, Climate Solutions.

**Education group only.** ~52 reviews. The `/education/reviews/` page is the source of truth for which reviews belong to the education coordinating group. Non-education reviews (255) were excluded 2026-06-15 with `exclude_reason=campbell_not_education_group`.

## Entry metadata (from WP REST API)

| Field | API key | Notes |
|-------|---------|-------|
| Title | `title.rendered` | |
| URL | `link` | `/review/{slug}/` |
| Full summary | `content.rendered` | HTML — structured sections (see below) |
| Excerpt | `excerpt.rendered` | Empty for most reviews |

**Content structure on review pages (4 standard sections):**
1. "What Is This [Review/Map] About?"
2. "What Studies Are Included?"
3. "What Are the Main Results?"
4. "What Do the Findings Mean?"

First section is the best source for a description blurb.

## Scraping instructions

**Config:** `sources/campbell-collaboration.json` — uses `url_filter` to fetch the education group page first, extract allowed slugs, then keep only matching API results.

**Command:** `python scripts/scrape.py campbell-collaboration`

The scraper paginates the full API (4 pages, 307 reviews), then applies the URL filter to keep only the ~52 education reviews. `content.rendered` contains the full plain-language summary as HTML. No individual page fetches needed.

## Quirks

- `excerpt.rendered` is empty for all reviews — use `content.rendered` instead
- 458 sitemap URLs vs 307 API results: gap is protocols, titles, and withdrawn reviews still in WP
- Individual review pages are plain-language summaries, not full systematic reviews (those are on Wiley)
- No author bylines or DOIs on Campbell's own pages
- 11 coordinating groups serve as informal taxonomy
