# National Academies Press (NAP / NASEM)

## Discovery

- **Method:** Not yet viable with current tooling
- **Old domain:** `https://nap.nationalacademies.org/` (301-redirects to new domain)
- **New domain:** `https://www.nationalacademies.org/publications/all`
- **Total:** ~15,375 total publications; ~961 education-related
- **Platform:** Custom CMS — publications page is JS-rendered

## Access

- **robots.txt (nap.nationalacademies.org):** Explicitly blocks AI crawlers — `anthropic-ai`, `Claude-Web`, `ClaudeBot`, `GPTBot`, `Google-Extended`, `CCBot`, `PerplexityBot` all disallowed.
- **robots.txt (nationalacademies.org):** Blocks all URLs with query parameters. Crawl-delay: 10 seconds.
- **llms.txt:** None (404).
- **Sitemap:** Empty/inaccessible on nap subdomain.
- **Authentication:** Metadata freely accessible. PDF download may require guest registration.

## Scope

Consensus study reports, proceedings, and other publications from the National Academies of Sciences, Engineering, and Medicine. Education subtopics: Academic Standards & Testing, Athletics & Physical Activity, Educational Administration, English Language Learning, Higher Education, Pre-K to Grade 12, School Safety, Teacher Development, Technical Education.

## Status: Not currently scrapable

**Tested 2026-06-15:** The publications catalog at `nationalacademies.org/publications/all` is JS-rendered — static fetch returns publication card wrappers but no actual titles, descriptions, or links. Topic filtering is also JS-driven (query params don't filter server-side). Would require Playwright.

Additionally, the old domain (nap.nationalacademies.org) explicitly blocks AI crawlers in robots.txt. The new domain doesn't block AI specifically but has restrictive query-string rules and a 10s crawl-delay.

**Current indexed:** 2 entries (manually added). DOI pattern `10.17226/{ID}` is consistent and useful for deduplication.

**Path forward:** Playwright scraping of the new domain, or manual curation of landmark education reports. Individual publication pages (e.g., `/publications/25389`) may be server-rendered — untested.

## Entry metadata (from individual publication pages, if accessible)

| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | |
| Type | Yes | Consensus Study Report, Proceedings, etc. |
| Year | Yes | |
| DOI | Yes | `10.17226/{ID}` pattern |
| ISBNs | Yes | |
| Description | Yes | Multi-sentence summary |
| Committee | Yes | Named members |
| Page count | Yes | |
| PDF | Sometimes | May require registration |

## Quirks

- Domain migration in progress: nap.nationalacademies.org → nationalacademies.org
- Old domain robots.txt is more restrictive than new domain
- Old URL pattern `/catalog/{ID}/{slug}` redirects to new `/publications/{ID}`
- Massive catalog (15K+) — education subset (~961) needs topic filtering that only works client-side
