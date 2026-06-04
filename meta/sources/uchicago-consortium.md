# UChicago Consortium on School Research

## Discovery

- **Method:** Paginated HTML listing
- **URL:** `https://consortium.uchicago.edu/publications?page={N}` (pages 0–31, 10 items/page)
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

**Pass 1:** Paginate through `?page=0` to `?page=31`. Extract title, URL, type, date from each item. Most items will lack adequate blurbs and go to backlog.

**Pass 2:** Fetch individual pages for backlog items to get abstracts, authors, and tags.

## Quirks

- URL slugs preserve some capitalization (e.g., `Chicago`, `COVID-19`)
- No sitemap — pagination is the only discovery mechanism
- Type labels are inconsistent — not every listing item shows one
