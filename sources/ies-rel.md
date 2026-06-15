# IES Regional Education Labs (REL)

## Discovery

- **Method:** Not directly scrapable — JS SPA. ERIC API is the viable proxy.
- **Products page:** `https://ies.ed.gov/ncee/rel/Products` — JavaScript SPA, returns empty shell on static fetch
- **ERIC API:** `https://api.ies.ed.gov/eric/?search=source:"Regional+Educational+Laboratory"&rows=100&format=json` — 1,134 results
- **Platform:** Drupal (new IES site) with JS SPA for the products section
- **10 regions:** Appalachia, Central, Mid-Atlantic, Midwest, Northeast & Islands, Northwest, Pacific, Southeast, Southwest, West

## Access

- **robots.txt:** Standard Drupal. No blocks on `/ncee/` or REL paths. No AI bot restrictions.
- **llms.txt:** None.
- **Sitemap:** `sitemap.xml` has ~7,000 URLs total but zero `/ncee/rel/` product URLs — REL products not indexed in sitemap.
- **Authentication:** None — .gov site, fully open.

## Scope

Applied research, technical assistance, and data analysis produced by the 10 Regional Education Labs. Topics span K-12 education improvement: evidence-based practice, state/district policy, teacher effectiveness, school improvement, early childhood, STEM, literacy, college readiness.

## Status: ERIC API as proxy

**Tested 2026-06-15:** The Products page at `/ncee/rel/Products` is a JavaScript SPA — static HTML fetch returns only the page shell with no product data. No XHR API endpoints discoverable from the page source. Regional product pages also appear JS-rendered.

**ERIC API works:** `api.ies.ed.gov/eric/` with `source:"Regional Educational Laboratory"` returns 1,134 results with titles, descriptions, and ERIC IDs. This is the most viable discovery path.

**Current indexed:** 30 entries.

## Entry metadata (from ERIC API)

| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | |
| Description | Yes | Abstract/summary |
| ERIC ID | Yes | e.g., ED612345 |
| URL | Sometimes | Not all records have direct URLs |
| Authors | Yes | |
| Date | Yes | Publication year |
| Source | Yes | Specific REL region name |
| Subject descriptors | Yes | ERIC controlled vocabulary |
| Publication type | Yes | Reports, Briefs, etc. |

## Scraping instructions

**Via ERIC API:** Paginate with `start` parameter (100 per page, ~12 pages). Filter by `source:"Regional Educational Laboratory"`. ERIC provides abstracts and metadata but not always direct URLs to the REL product page — may need to construct URLs from ERIC IDs or titles.

**Alternative (future):** Playwright could render the Products SPA directly. The SPA likely calls an internal API that could be reverse-engineered from browser dev tools.

## Quirks

- The IES site is transitioning from old `/ncee/rel/` paths to new Drupal paths under `/use-work/regional-educational-laboratories-rel/`
- ERIC is the authoritative proxy but URL mapping is imperfect — some ERIC records link to PDFs, not REL product pages
- 10 regional labs produce content independently — no single editorial standard
- Product count (1,134 via ERIC) spans many years; not all may still have live pages
