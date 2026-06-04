# Learning Policy Institute (LPI)

## Discovery

- **Method:** Paginated HTML listings, split by publication type
- **Reports:** `https://learningpolicyinstitute.org/products/reports?page={N}` — 17 pages, ~167 items
- **Briefs:** `https://learningpolicyinstitute.org/products/briefs?page={N}` — 14 pages, ~139 items
- **Fact sheets:** `https://learningpolicyinstitute.org/products/fact-sheets?page={N}` — 4 pages, ~41 items
- **Total:** ~347 research publications (excluding blog posts and videos)
- **Platform:** Drupal, server-rendered — no JS required

## Access

- **robots.txt:** Standard Drupal. Product/listing pages not blocked. No crawl-delay.
- **llms.txt:** None (404).
- **Sitemap:** Exists but nearly useless — only 26 `/product/` URLs out of ~500. Do not use.
- **API:** No JSON:API endpoint (returns 404).
- **Authentication:** None required.

## Scope

Research publications: reports, briefs, and fact sheets. Topics include community schools, educator quality, school finance, SEL, deeper learning, early childhood, school safety, assessment, equity. Blog posts (~201) are out of scope unless individually notable.

## Entry metadata

**From listing pages (all three types):**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Linked text |
| URL | Yes | `/product/{slug}` |
| Authors | Yes | Plain text |
| Date | Yes | Month DD, YYYY |
| Blurb | Yes | 1-2 sentence description |
| Type | Yes | Determined by which listing page |

**From individual pages** (`/product/{slug}`):
| Field | Available |
|-------|-----------|
| Full abstract | Yes (multi-paragraph) |
| DOI | Yes |
| Topics/tags | Yes |
| PDF downloads | Yes |
| License | Yes (CC BY-NC 4.0) |

## Scraping instructions

**Pass 1:** Paginate through all three listing types (35 pages total). Listing pages provide title, URL, authors, date, and blurb — usually adequate for indexing without individual page fetches.

**Pass 2:** Only needed for items with blurbs under the threshold.

## Quirks

- Three separate listing endpoints by type — not one unified listing
- Items per page: 10 for reports/briefs, 11-12 for fact sheets
- Slug conventions vary by type: `-report`, `-brief`, `-factsheet` suffixes
- `/research` is equivalent to `/products/reports` (same content, same pagination)
- Sitemap is severely incomplete — do not rely on it
