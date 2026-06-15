# Journal of Learning Analytics (JLA)

## Discovery

- **Method:** Archive page → issue pages (OJS standard)
- **Archive:** `https://learning-analytics.info/index.php/JLA/issue/archive` — 35 issues listed
- **Total:** ~300-350 articles (average ~9-10 per issue)
- **Platform:** Open Journal Systems (OJS) by PKP
- **Date range:** Vol 1 No 1 (2014) through Vol 13 No 1 (2026)

## Access

- **robots.txt:** Only `/cache/` disallowed. **Crawl-delay: 60 seconds.** No AI bot blocks.
- **llms.txt:** None (404).
- **Sitemap:** None (404).
- **Authentication:** None — fully open access.

## Scope

Peer-reviewed research on learning analytics: predictive modeling, dashboards, self-regulated learning, discourse analytics, institutional analytics, ethics of learning data. Published by SoLAR (Society for Learning Analytics Research).

## Entry metadata

**From issue table-of-contents pages:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | `<h3>` elements with links |
| URL | Yes | `/index.php/JLA/article/view/{ID}` |
| Authors | Yes | Text below title (no semantic wrapper) |
| Page range | Yes | Inline text |

**From individual article pages:**
| Field | Available | Notes |
|-------|-----------|-------|
| Abstract | Yes | Full abstract on article page |
| Keywords | Yes | Listed on article page |
| DOI | Yes | In `citation_doi` meta tag |
| PDF URL | Yes | In `citation_pdf_url` meta tag |
| Volume/Issue | Yes | Breadcrumb and metadata |

## Scraping instructions

**Two-step:** Fetch archive page for all issue URLs, then fetch each issue page for article listings. Individual article pages needed for abstracts (not shown on issue pages). Respect the 60-second crawl-delay — this means ~35 minutes for all issue pages, plus time for individual articles.

OJS standard `<meta>` tags (`citation_title`, `citation_author`, `citation_doi`, `citation_pdf_url`) on article pages are the most reliable metadata source.

## Quirks

- 60s crawl-delay is significant — full scrape takes hours
- Issue IDs are non-sequential (307, 485, 515, 517, ...)
- Some issue IDs return login page rather than 404
- "Early Access" issue contains pre-publication articles
