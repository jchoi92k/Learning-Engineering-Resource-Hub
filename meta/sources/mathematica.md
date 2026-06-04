# Mathematica

## Discovery

- **Method:** Coveo REST API (proxied through site, no auth needed)
- **Endpoint:** `https://mathematica.org/coveo/rest/search/v2`
- **Query:** `@mprdisplaytemplatename=Publication @mprhumanservicetopicsv2=Education`
- **Total:** ~820 unique education publications
- **Pages:** ~82 (10 results per page, enforced max)

## Access

- **robots.txt:** Only `/User/*` blocked. No crawl-delay.
- **llms.txt:** None (404).
- **Authentication:** None required. The existing docs claiming "requires bearer token" are incorrect — the site's Coveo proxy accepts unauthenticated GET requests.
- **Sitemap:** None exists. Coveo API is the only discovery method.

## Scope

IES-funded RCTs, quasi-experimental studies, and other education research publications. Sub-topics include Teacher/Principal Effectiveness, College/Career Readiness, Literacy/Numeracy, School Choice, STEM, Special Education, Postsecondary.

Publication categories: Project Report (645), Brief (234), Journal Article (226), Fact Sheet (121), Working Paper (68), Presentation (64), and others.

Current indexing: 32 entries. Gap: ~788.

## Entry metadata (from Coveo response)

| Field | Coveo key | Notes |
|-------|-----------|-------|
| Title | `raw.systitle` | |
| URL | `raw.mprrelativeurl` | Uses staging domain — replace `staginginter.mathematica.net` with `mathematica.org` |
| Authors | `raw.mprauthors` | Array |
| Summary | `raw.mprsummary` | Paragraph-length abstract |
| Date | `raw.mprcomputedcontentdate` | Epoch milliseconds |
| Sub-topics | `raw.mprhseducationtopicsv2` | Array |
| Category | `raw.mprpublicationcategories` | e.g., "Project Report", "Journal Article" |
| PDF link | `raw.mprpublicationurl` | External URL or media item ID |

## Scraping instructions

**Paginate the Coveo API.** Step `firstResult` by 10 each request. Use `enableDuplicateFiltering=true` (the index has master/internet Sitecore duplicates). Sort by `@mprcomputedcontentdate descending` for incremental updates.

Full query:
```
GET /coveo/rest/search/v2?q=&firstResult={N}&numberOfResults=10&aq=@mprdisplaytemplatename=Publication @mprhumanservicetopicsv2=Education&enableDuplicateFiltering=true&sortCriteria=@mprcomputedcontentdate descending
```

All metadata needed for indexing is in the API response — no individual page fetches required.

## Quirks

- 10 results per page is the enforced max — `numberOfResults` above 10 is ignored
- Duplicates exist from Sitecore master/internet databases; deduplicate by slug after fetching
- URLs use staging domain (`staginginter.mathematica.net`) — must transform to `mathematica.org`
- "Education" is a sub-topic under "Human Services" focus area, not a top-level category
- Date is epoch milliseconds, not ISO string
