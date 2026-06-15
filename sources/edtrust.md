# The Education Trust

## Discovery

- **Method:** Sitemap + type filtering
- **Primary URL:** `https://edtrust.org/research-tools-and-i-sitemap.xml` (582 `/rti/` URLs)
- **Alternative:** WP REST API at `https://edtrust.org/wp-json/wp/v2/research-tools-and-i` (caps at ~6 items/page, ~64 pages, returns fewer items than sitemap)
- **Pagination:** Sitemap is single-page. API uses `?page=N`.
- **Total items:** 582 RTI URLs in sitemap; ~318 are research-like
- **Items per request:** All 582 URLs from one sitemap fetch

## Access

- **Rendering:** Individual resource pages are server-rendered HTML. No JS needed.
- **Playwright:** Not needed
- **robots.txt:** Permissive. Only `/wp-admin/`, `/trackback/`, `/xmlrpc.php`, `/feed/` blocked.
- **llms.txt:** Not found
- **Rate limits:** None observed. API hard-caps at 6 items/response regardless of `per_page` param.

## Scope

- **Coverage strategy:** Research-like content only (~318 items)
- **Include types:** Report (110), Brief (74), Guide (58), Compilation (32), Fact Sheet (25), Data Tool (11), Digital Report (4), Infographic (4)
- **Exclude types:** Blog Post (755), Press Releases (250), Public Statements (188), Public Letters (102), Public Comments (94), Op-Ed (22), Podcast (29), Video (39), State News (18), Public Testimony (23), Campaign (7)
- **Current indexed:** 31
- **Estimated remaining:** ~287
- **Type taxonomy:** `type-of-content` (19 terms). API endpoint: `https://edtrust.org/wp-json/wp/v2/type-of-content?per_page=100`

## Entry metadata

**From individual pages (server-rendered):**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full |
| URL | Yes | `/rti/{slug}/` |
| Date | Yes | Full date |
| Description | Yes | Opening paragraph — rich |
| Content type | Yes | In breadcrumb |
| Topics | Yes | Taxonomy terms |
| Authors | Yes | Byline |
| PDF link | Yes | `/wp-content/uploads/...` |

**From API:** Returns title, date, link, content (HTML), taxonomy IDs (need separate resolution), Yoast meta.

**Description approach:** Must fetch individual pages — no listing page exists (the `/research/` URL redirects to a single press release, and `/search/` is JS-only).

## Scraping instructions

```
1. Fetch https://edtrust.org/research-tools-and-i-sitemap.xml
2. Extract all <loc> URLs (582 /rti/ paths)
3. For each URL, fetch the page and extract:
   - Title
   - Date
   - Description (first paragraph of content)
   - Content type (breadcrumb label)
   - Topics
   - Authors
   - PDF link (if present)
4. Filter: keep only items where content type is one of:
   Report, Brief, Guide, Compilation, Fact Sheet, Data Tool,
   Digital Report, Infographic
5. Compare against existing entries in llms-full.txt
6. Stage new entries in docs/staging/edtrust.txt
```

## Quirks

- `/research/` is NOT a listing page — it resolves to the most recent news item tagged "research."
- `/search/` is entirely JS-driven (Algolia-like). No server-rendered results. Hash-based URL fragments for filters.
- WP REST API hard-caps responses at ~6 items regardless of `per_page`. Unreliable for full enumeration.
- The "1,903" resource count includes all post types across the site (blog, press-room, news, RTI). The RTI-specific sitemap has 582.
- Four regional subdomains exist (midwest, west, newyork) with their own sitemaps — currently out of scope.
