# NWEA Research

## Discovery

- **Method:** WordPress REST API, post type `publications`, plus one page fetch per new item for the abstract (since 2026-08-30; the sitemap route below carries no metadata)
- **Primary URL:** `https://www.nwea.org/wp-json/wp/v2/publications?per_page=100&orderby=date&order=desc` (317 items in 4 pages on 2026-08-30)
- **Alternative:** `https://www.nwea.org/publication-sitemap.xml` (547 URLs as of 2026-06-04) — discovery only. The listing at `/research/all-research/` 404s after page 9.
- **Pagination:** API `?page=N`; `per_page=100` is honoured and the run stops on a short page. Newest-first, so `early_stop` is declared.
- **Total items:** 317 publications in the API (2026-08-30); `research_type`, `research_theme`, `research_product`, `research_center` and `bio_link` are resolved to names via `lookups`
- **Items per request:** 100 from the API; the abstract needs the item page (`detail_fetch`)

## Access

- **Rendering:** Server-rendered HTML (WordPress/Yoast). No JS needed.
- **Playwright:** Not needed
- **robots.txt:** Very permissive. Only `/wp/wp-admin/` blocked. Yoast block allows everything.
- **llms.txt:** Not found
- **Rate limits:** None observed

## Scope

- **Coverage strategy:** Index all publications
- **Current indexed:** 309 after the 2026-08-30 backfill via the WordPress REST post type `publications` (`scrape.py nwea-research --backfill`: 4 API pages + 5 taxonomy lookups + 247 page fetches for the abstracts, 250 requests, every URL once, 5 s gaps): 239 inserted with page abstracts (`page-abstract`; two templates — `div.description_wrap` or the paragraph after the Description heading), taxonomies resolved to names (type, themes, products, centers), the page's author line and date captured, publication block kept as `page_text`; 8 pages without an abstract are pending rows. `type_allow` lists all 15 real labels so a new label gets recorded rather than silently indexed. The API replaces the sitemap discovery; the sitemap remains a cross-check.
- **Estimated remaining:** ~477
- **Filters available on listing page:** Topic (28+), Researcher (26+), Type (13), Center (3), Product (3). URL params work: `?publication_type=journal-article`

## Entry metadata

**From listing pages (pages 1-9 only):**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full, linked |
| URL | Yes | `/research/publication/{slug}/` |
| Type | Yes | Badge (Research brief, Technical brief, White paper, Guide, etc.) |
| Blurb | Yes | 1-2 sentences — substantive |
| Authors | Yes | Linked names with credentials |
| Year | Yes | Publication year |
| Topics | Yes | Multiple linked tags |
| Products | Yes | MAP Growth, MAP Reading Fluency, etc. |

**From individual pages:**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full |
| Description | Yes | 1-2 paragraph abstract |
| Authors | Yes | Full names with credentials |
| Date | Yes | Month + year |
| Topics | Yes | Tags |
| Products | Yes | MAP suite products |
| PDF link | Yes | `/uploads/{slug}_NWEA_{type}.pdf` |
| Related pubs | Yes | Linked |

**Description approach:** Listing blurbs are substantive and usable. Individual pages provide richer abstracts. Since pagination breaks at page 9, most entries need individual page fetches anyway.

## Scraping instructions

Config-driven: `python scripts/scrape.py nwea-research` (config in `nwea-research.json`, rewritten 2026-08-30): WordPress REST post type `publications`, newest-first with `early_stop`; taxonomies resolved to names via `lookups`; `type_allow` is checked before any page is fetched; each new item's page is then fetched for the abstract (`detail_fetch`: `div.description_wrap`, or the paragraph after the Description heading; `page-abstract`) and its publication block is kept as `page_text` (`text_selector: div.txtcol`). Backfilled 2026-08-30 with `--backfill`. Run modes and the request audit: `sources/README.md`.

## Quirks

- Pagination breaks at page 10 — all pages 10+ return 404. This appears to be a WordPress permalink/rewrite rule bug. The sitemap is the only reliable way to get the full inventory.
- `/research/` is a curated hub page (featured research, team bios, etc.), not a pure listing. Use `/research/all-research/` for the listing or the sitemap for completeness.
- Type values: Research brief, Technical brief, White paper, Guide, Journal article, Blog article, Technical report, Book, Infographic, Podcast, Webinar, Video, other.
- 13 publication types across 547 items. Consider filtering out non-research types (Blog article, Podcast, Webinar, Video) if scope tightens.
