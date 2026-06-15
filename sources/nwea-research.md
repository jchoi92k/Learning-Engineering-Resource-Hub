# NWEA Research

## Discovery

- **Method:** Sitemap
- **Primary URL:** `https://www.nwea.org/publication-sitemap.xml` (547 URLs)
- **Fallback:** Listing page at `https://www.nwea.org/research/all-research/` (pagination breaks after page 9 — only ~63 items accessible)
- **Pagination:** Sitemap is single-page. Listing uses `/page/{N}/` but 404s after page 9.
- **Total items:** 547 (per sitemap, as of 2026-06-04)
- **Items per request:** All 547 from one sitemap fetch

## Access

- **Rendering:** Server-rendered HTML (WordPress/Yoast). No JS needed.
- **Playwright:** Not needed
- **robots.txt:** Very permissive. Only `/wp/wp-admin/` blocked. Yoast block allows everything.
- **llms.txt:** Not found
- **Rate limits:** None observed

## Scope

- **Coverage strategy:** Index all publications
- **Current indexed:** 70
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

```
1. Fetch https://www.nwea.org/publication-sitemap.xml
2. Extract all <loc> URLs (547 publication paths)
3. Compare against existing entries in llms-full.txt
4. For new URLs, fetch each individual page and extract:
   - Title (h1)
   - Type (badge/label)
   - Description (abstract paragraph)
   - Authors
   - Date (month + year)
   - Topics (tag links)
   - Products (if any)
5. Stage new entries in docs/staging/nwea-research.txt
```

## Quirks

- Pagination breaks at page 10 — all pages 10+ return 404. This appears to be a WordPress permalink/rewrite rule bug. The sitemap is the only reliable way to get the full inventory.
- `/research/` is a curated hub page (featured research, team bios, etc.), not a pure listing. Use `/research/all-research/` for the listing or the sitemap for completeness.
- Type values: Research brief, Technical brief, White paper, Guide, Journal article, Blog article, Technical report, Book, Infographic, Podcast, Webinar, Video, other.
- 13 publication types across 547 items. Consider filtering out non-research types (Blog article, Podcast, Webinar, Video) if scope tightens.
