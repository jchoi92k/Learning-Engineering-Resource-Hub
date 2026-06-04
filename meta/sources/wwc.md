# What Works Clearinghouse (WWC)

## Discovery

- **Method:** Single-page HTML listing (all results on one page)
- **Intervention reports:** `https://ies.ed.gov/ncee/wwc/Search/Products?productType=2` — 619 results
- **Practice guides:** `https://ies.ed.gov/ncee/wwc/Search/Products?productType=1` — 30 results
- **Total:** 649 (619 + 30)
- **Platform:** ASP.NET MVC, server-rendered — no JS required

## Access

- **robots.txt:** Standard Drupal (IES site wraps a Drupal front-end). `/ncee/` not blocked. No crawl-delay.
- **llms.txt:** None (404).
- **Sitemap:** Exists at `https://ies.ed.gov/sitemap.xml` but contains zero WWC URLs — the WWC app is a separate ASP.NET mount. Useless for discovery.
- **Authentication:** None required.

## Scope

All intervention reports and practice guides. Evidence-based education interventions reviewed by WWC. Includes evidence tier ratings (1–3), grade levels, topic areas.

## Entry metadata

**From listing page (single page, no pagination):**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Linked text with release date in parens |
| URL | Yes | `/ncee/WWC/InterventionReport/{id}` |
| Type | Yes | "Intervention Report" or "Practice Guide" |
| Grade level | Yes | e.g., "K-11", "PK", "9-12" |
| Evidence tier | Yes | 1, 2, or 3 |
| Description | Yes | 2-3 sentence summary |

**From individual pages** (`/ncee/WWC/InterventionReport/{id}`):
| Field | Available |
|-------|-----------|
| Last updated date | Yes |
| Outcome domain ratings | Yes |
| Demographic breakdown | Yes |
| Study count | Yes |
| PDF downloads | Yes |

## Scraping instructions

**Pass 1:** Fetch `?productType=2` once for all 619 intervention reports. Fetch `?productType=1` once for all 30 practice guides. Two HTTP requests total. Each result includes title, URL, grade level, evidence tier, and a 2-3 sentence description — usually adequate for indexing without individual page fetches.

**Pass 2:** Only needed for items with thin descriptions (unlikely — most have 2-3 sentences).

## Quirks

- All results on one page — no pagination. One request = full catalog.
- Report IDs are non-contiguous (11–733 for 619 reports). Do not enumerate IDs; extract from listing page.
- Invalid IDs return HTTP 500, not 404.
- Practice guide count is 30 (source-targets.json says 29 — a 30th was added Dec 2024, ID 31).
- URL case: path uses `/WWC/` (uppercase) in individual report URLs.
