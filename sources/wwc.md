# What Works Clearinghouse (WWC)

**Status (2026-08-30):** rated only. Intervention reports with an evidence tier (1–3) and the practice guides are published; every Tier −1 report (WWC found no studies meeting its standards) is held as an excluded `wwc_tier_minus1_no_evidence` row, whether or not the listing carries a description. Two configs, both in the weekly list: `wwc.json` (intervention reports, `exclude_when` on `evidence_tier`) and `wwc-practice-guides.json` (`productType=1`, `type_default` Practice Guide).

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

## Exclusion: Tier -1 entries (no qualifying studies)

Of 619 intervention reports, **475 are evidence tier -1** — meaning WWC searched for studies but found none meeting their standards. These pages contain only "no studies of [X] were found that met WWC design standards." They have no description on the listing page and no substantive content on the detail page.

**Decision (2026-06-15):** Tier -1 entries are excluded from published output. They are in hub.db with `excluded=1, exclude_reason='wwc_tier_minus1_no_evidence'` for dedup purposes. Future scrapes should not re-index them. See `private/decisions.md` for full rationale.

**Published:** the intervention reports with evidence tiers 1–3 (144 on 2026-08-30) plus the practice guides. Until 2026-08-30 the hold reached only Tier −1 reports without a listing description; 203 with one were published, and were held that day.

## Scraping instructions

**Pass 1:** `scrape.py wwc` fetches `?productType=2` once for all 619 intervention reports; `scrape.py wwc-practice-guides` fetches `?productType=1` once for all 30 practice guides. Two HTTP requests total (plus robots.txt). Each result includes title, URL, grade level, evidence tier, and a 2-3 sentence description — usually adequate for indexing without individual page fetches. Skip tier -1 entries (no descriptions, excluded by policy).

**Pass 2:** Not needed. Detail pages are JS-rendered (content loaded client-side), so raw fetches return empty containers. The listing page description is the best source. Playwright would be required for detail pages, but tier 1/2/3 entries already have adequate descriptions from the listing.

## Quirks

- All results on one page — no pagination. One request = full catalog.
- Report IDs are non-contiguous (11–733 for 619 reports). Do not enumerate IDs; extract from listing page.
- Invalid IDs return HTTP 500, not 404.
- Practice guide count is 30 (source-targets.json says 29 — a 30th was added Dec 2024, ID 31).
- URL case: path uses `/WWC/` (uppercase) in individual report URLs.
