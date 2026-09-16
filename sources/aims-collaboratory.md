# AIMS Collaboratory

## Discovery

- **Method:** Sitemap
- **Sitemap:** `https://www.aimscollaboratory.org/sitemap.xml` — ~160 URLs (60 project teams + 100 resources)
- **Listing pages:** `/project-teams-all` and `/resources-all` (paginated, ~20/page)
- **Total:** ~160 items
- **Platform:** Squarespace

## Access

- **robots.txt:** Blocks AI crawlers — ClaudeBot, GPTBot, Amazonbot, Bytespider explicitly disallowed. Standard search engines allowed.
- **llms.txt:** None (404).
- **Authentication:** None required for public pages. Member Hub on Mighty Networks is separate and gated.

## Scope

Learning engineering project teams and resources: code/algorithms, tools, whitepapers, datasets, frameworks. Formerly LearnPlatform — brand transition complete.

## Status: No further scraping

**Decision (2026-06-15):** Respecting robots.txt AI crawler block. The 53 entries already indexed are retained but no future automated scraping will be done. Manual additions are acceptable if individually sourced.

## Entry metadata

**From individual resource pages:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Page heading |
| URL | Yes | `/resources-all/{slug}` or `/project-teams-all/{slug}` |
| Author | Yes | Usually "Jeremy Koren" (content manager) |
| Date | Yes | Publication date |
| Category | Yes | Code/Algorithm, Tool, Whitepaper, etc. |
| Description | Yes | Purpose/abstract sections on page |
| Grade level | Sometimes | Audience tags |
| Research area | Yes | Platform/Program, Implementation, Data use, AI |

## Quirks

- `source-targets.json` has `discovery_url: https://aimscollab.org/` — actual domain is `https://www.aimscollaboratory.org/`
- Squarespace pagination uses Unix timestamp offsets, not page numbers
- No REST API — Squarespace doesn't expose one for content
- Resources and project teams are separate content types with different structures

## Metadata backfill (2026-09-16)

Metadata backfill 2026-09-16: `sources/aims-collaboratory.json` (`discovery: db`, `from_db.host_allow`) fetched the 34 rows on open repository / organisation hosts once (35 requests, one dropped connection); the AIMS site itself is still not scraped. Dates, authors and PDF links come from the pages' citation / bepress / Dublin Core meta tags (`page-meta`): 19 rows; ten e4.northwestern.edu posts are dated from their permalink path (`date_source: url`). 29/48 dated in all; the rest are code / platform entries (date n/a) or pages without metadata (EDM proceedings, ACL Anthology, NORC event, EdInstruments toolkit). Commercial-publisher hosts (Springer, ACM, Sage, Emerald, MDPI, NBER) were left out.
