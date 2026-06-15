# CASEL (Collaborative for Academic, Social, and Emotional Learning)

## Discovery

- **Method:** Paginated HTML listing
- **Listing:** `https://casel.org/news-publications/sel-publications/` — 25 items/page, 14 pages
- **Pagination:** `https://casel.org/news-publications/sel-publications/page/{N}/`
- **Total:** ~327 publications
- **Platform:** WordPress (Yoast SEO), server-rendered

## Access

- **robots.txt:** Standard WP — blocks `/wp-admin/`, `/wp-includes/`, search (`/?s=`). **Crawl-delay: 60 seconds.** No AI bot blocks.
- **llms.txt:** None (404).
- **Sitemap:** `sitemap_index.xml` exists (Yoast) — 60 posts, 160 blog posts, 80 pages. No custom publication sitemap.
- **WP REST API:** Standard endpoints work (`/wp-json/wp/v2/posts` — 58, `/pages` — 80) but publications are **not** a custom post type — no `/wp-json/wp/v2/publications` endpoint. Must scrape HTML.
- **Authentication:** None — fully open access.

## Scope

SEL publications: research reports, briefs, frameworks, guides, infographics, videos. Topics include school districts, classrooms, state policy, adult SEL, mental health, equity, college/career readiness, transformative SEL, literacy.

**Formats:** Articles & Briefs, Books & Chapters, Infographics, Reports & Guidance, Videos.

## Entry metadata

**From listing page:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Linked text |
| URL | Yes | Full URL to publication page |
| Topic tags | Yes | Filter categories visible in page |

**From individual publication pages:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | Page heading |
| Description | Yes | Introductory paragraph(s) |
| Topics | Yes | Tag links |
| Format | Yes | Publication type |
| External links | Sometimes | Many publications link to external PDFs or partner sites |

## Scraping instructions

**Config:** `sources/casel.json` — pagination with `detail_fetch` (listing pages have no descriptions, so scrape.py fetches each individual page for `og:description`).

**Command:** `python -u scripts/scrape.py casel`

**Step 1:** Paginate listing pages (14 pages, 25 items each) for URLs and titles. **Step 2:** `detail_fetch` hits each individual publication page for the meta description. Respects 60-second crawl-delay from robots.txt — full scrape of ~327 items takes ~5.5 hours. Progress saves after every fetch; safe to Ctrl+C and resume.

After scraping: `python scripts/process_staged.py casel` then `python scripts/build_from_db.py`.

Some publication URLs point to external sites (e.g., publisher pages for books/chapters). These should be flagged but can still be indexed with the CASEL page as the canonical URL.

## Quirks

- 60s crawl-delay is significant
- Publications are not a WP custom post type — no REST API shortcut
- Some items link to external publishers rather than hosting content directly
- Blog posts (160) are separate from publications (327) — index publications only unless a blog post is individually notable
- The "Research" page (`/fundamentals-of-sel/what-does-the-research-say/`) is narrative, not a searchable database
