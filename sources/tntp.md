# TNTP

## Discovery

- **Method:** Sitemap
- **Primary URL:** `https://tntp.org/publication-sitemap.xml`
- **Fallback:** Listing page at `https://tntp.org/publications/` (shows 30 of 36 — misses 6)
- **Pagination:** None needed — sitemap has all 36 URLs on one page
- **Total items:** 36 (as of 2026-06-04)
- **Items per request:** All 36 in one sitemap fetch

## Access

- **Rendering:** Server-rendered HTML (WordPress). No JS needed.
- **Playwright:** Not needed. Topic filter pages at `/search-results-publications/?topic=*` are JS-rendered, but they're unnecessary — sitemap covers everything.
- **robots.txt:** Very permissive. Only `/wp-admin/` and one specific PDF blocked. No AI restrictions.
- **llms.txt:** Exists at `https://tntp.org/llms.txt`. Explicitly encourages AI indexing of publications.
- **Rate limits:** None observed

## Scope

- **Coverage strategy:** Index all (small corpus)
- **Current indexed:** 36
- **Estimated remaining:** 0 (complete)
- **Update cadence:** Check sitemap quarterly for new publications

## Entry metadata

**From listing page (`/publications/`):**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full |
| URL | Yes | `/publication/{slug}/` |
| Date | Yes | Full date |
| Blurb | Yes | 1 sentence (~10-20 words) — thin but usable |
| Topics | Yes | 1-2 per item |
| Authors | No | Not on listing |

**From individual pages:** 150-200+ word descriptions, richer metadata.

**Description approach:** Listing blurbs are thin. For new entries, fetch individual publication pages for richer descriptions.

## Scraping instructions

```
1. Fetch https://tntp.org/publication-sitemap.xml
2. Extract all <loc> URLs matching /publication/*
3. Compare against existing entries in llms-full.txt
4. For new URLs, fetch each individual page and extract:
   - Title (h1)
   - Description (opening paragraph or meta description)
   - Date
   - Topics (tag links)
5. Stage new entries in docs/staging/tntp.txt
```

## Quirks

- The listing page (`/publications/`) only shows 30 of 36 publications. Always use the sitemap for the complete inventory.
- Topic filter pages (`/search-results-publications/?topic=*`) return zero results via static fetch — they're JS-rendered. Irrelevant since the sitemap is complete.
