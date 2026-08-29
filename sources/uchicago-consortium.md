# UChicago Consortium on School Research

## Discovery

- **Method:** Paginated HTML listing
- **URL:** `https://consortium.uchicago.edu/publications?page={N}` (pages 0–31+, 10 items/page, newest first)
- **Total:** 319 publications confirmed
- **Platform:** Drupal, server-rendered — no JS required
- **No sitemap** (returns 404). No API (Drupal JSON:API disabled).

## Access

- **robots.txt:** Standard Drupal. `/publications` not blocked. No crawl-delay.
- **llms.txt:** None (404).
- **Authentication:** None required.

## Scope

All 319 publications. Types include Report, Article, Brief, Field Scan, Book, Snapshot. Focus: K-12 school improvement, equity, attendance, 5Essentials survey, Chicago Public Schools.

## Entry metadata

**From listing page:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Linked text |
| URL | Yes | `/publications/{slug}` |
| Type | Partial | Not always present |
| Date | Yes | Month + year |
| Blurb | Partial | Some items have subtitles, many don't |
| Authors | No | Only on individual pages |

**From individual pages** (`/publications/{slug}`):
| Field | Available |
|-------|-----------|
| Authors | Yes (with links to staff pages) |
| Description | Yes (multi-sentence abstract) |
| Tags | Sometimes (under "Publication Tags") |
| PDF downloads | Yes (direct links) |

## Scraping instructions

Config-driven since 2026-08-28: `python scripts/scrape.py uchicago-consortium` (config in `uchicago-consortium.json`).

- Paginates `?page=0`, `?page=1`, … (10 items/page) and stops early once a page is mostly already-indexed (3 consecutive / 5 total known URLs). `--pages N` is a hard cap.
- The listing carries no description (at most a subtitle), so **every new item is detail-fetched**: `detail_fetch` reads `meta[property='og:description']` from the publication page, which holds the full abstract (~300–1,300 chars). Same pattern as CASEL. Cost is bounded by early-stop — a weekly run fetches only the handful of new pages.
- Then `python scripts/process_staged.py uchicago-consortium` → `python scripts/build_from_db.py`.
- In the weekly automation source list (approved 2026-08-28).

Access re-checked 2026-08-28: robots.txt standard Drupal (no `/publications` block, no crawl-delay); llms.txt 404; no sitemap; `--test` passes with 10 items on page 0.

## Quirks

- URL slugs preserve some capitalization (e.g., `Chicago`, `COVID-19`)
- No sitemap — pagination is the only discovery mechanism
- Type labels are inconsistent — not every listing item shows one
