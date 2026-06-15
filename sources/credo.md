# CREDO at Stanford

## Discovery

- **Method:** Sitemap + category listing pages
- **Sitemap:** `https://credo.stanford.edu/report_type-sitemap.xml` — 88 report URLs
- **Category pages:** `/research-reports/charter-studies/` (9), `/research-reports/city-studies/` (~30), `/research-reports/covid-19-research/` (4-5), others
- **Report Finder:** `/research-reports/report-finder/` — only shows 9 featured reports, not the full catalog
- **Total:** ~88 reports (not 9 as previously estimated)
- **Platform:** WordPress (Yoast SEO), server-rendered — no JS required

## Access

- **robots.txt:** Fully permissive. No directories blocked.
- **llms.txt:** None (404).
- **Authentication:** None required.
- **Sitemap:** `sitemap_index.xml` exists, `report_type-sitemap.xml` has all report URLs.

## Scope

Charter school effectiveness research: national studies, state-level analyses, city studies, COVID impact, school closure effects, CMO evaluations. All institutional authorship ("CREDO at Stanford University").

## Entry metadata

**From category listing pages:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Linked text |
| URL | Yes | `/reports/item/{slug}/` |
| Tags | Yes | Category labels (Charter Study, City Study, COVID, etc.) |
| Date | Sometimes | Inconsistent placement |
| Blurb | Yes | 1-2 sentence description |

**From individual report pages:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | In h1 |
| Description | Varies | Some have multi-sentence descriptions, many older reports have none |
| PDF links | Yes | `/wp-content/uploads/...` |
| Authors | No | Institutional authorship only |
| Date | Inconsistent | Better on listing pages or in PDF filenames |

## Scraping instructions

**Hybrid approach:** Use sitemap for the complete URL inventory (88 reports). Use category listing pages for metadata (blurbs, tags, dates). Individual page fetches needed for reports not covered by category pages.

Many older/state-level reports have thin descriptions — expect significant backlog.

## Quirks

- Report Finder page shows only 9 "featured" reports — not the full catalog
- Category listing pages are the best metadata source (better blurbs than individual pages)
- Descriptions on individual pages range from ~27 words to ~200 words; some have only CREDO boilerplate
- No named authors — all institutional
- source-targets.json had ~9; actual count is ~88
