# Digital Promise

## Discovery

- **Method:** DSpace REST API (no browser rendering needed)
- **Primary URL:** `https://digitalpromise.dspacedirect.org/server/api/discover/search/objects?dsoType=item&size=100&page={0,1,2}`
- **Pagination:** 0-indexed `page` param, `size` param (max effective: 100). Full corpus in 3 requests.
- **Total items:** 258 (as of 2026-06-04)
- **Items per request:** 100

## Access

- **Rendering:** Angular SPA for human UI, but REST API returns structured JSON — no rendering needed
- **Playwright:** Not needed. Previous assumption was wrong; the API gives everything.
- **robots.txt:** Permissive. `/server/api/` is not disallowed. Only `/search`, `/admin/*`, `/submit`, etc. are blocked.
- **llms.txt:** Not found
- **Rate limits:** None observed. No crawl-delay in robots.txt.
- **Auth:** API is anonymous. Note: `WebFetch` (browser-like UA) gets 403'd — use `curl` or Python `requests` with a standard user agent.

## Scope

- **Coverage strategy:** Index all items
- **Current indexed:** 254
- **Estimated remaining:** ~4
- **Filtering:** None needed — corpus is small and entirely within scope

## Entry metadata

**From API (`dc.*` fields in discovery response):**

| Field | API path | Coverage |
|---|---|---|
| Title | `dc.title` | 100% |
| URL | `dc.identifier.uri` (handle URL) | 100% |
| Date | `dc.date.issued` | 100% |
| Description | `dc.description.abstract` (84%) + `dc.description` fallback (19%) | 99% combined |
| Authors | `dc.contributor.author` | 97% |
| Type | `dc.type` | 95% |
| Tags/subjects | `dc.subject` | 84% |
| DOI | `dc.identifier.doi` | 31% |

**Public URL pattern:** `https://digitalpromise.dspacedirect.org/items/{uuid}` or handle URL from `dc.identifier.uri`

**Description approach:** API abstracts are rich (3-8 sentences). Use the first 1-2 sentences.

## Scraping instructions

```
1. Fetch 3 pages of the discovery API:
   GET https://digitalpromise.dspacedirect.org/server/api/discover/search/objects?dsoType=item&size=100&page=0
   GET ...&page=1
   GET ...&page=2

2. For each item in _embedded.searchResult._embedded.objects[]:
   - Navigate to _embedded.indexableObject
   - Extract:
     title:   metadata["dc.title"][0].value
     url:     metadata["dc.identifier.uri"][0].value
     date:    metadata["dc.date.issued"][0].value
     desc:    metadata["dc.description.abstract"][0].value
              (fallback: metadata["dc.description"][0].value)
     authors: metadata["dc.contributor.author"][*].value
     type:    metadata["dc.type"][0].value
     tags:    metadata["dc.subject"][*].value
     uuid:    uuid (top-level)

3. Map dc.type to our type taxonomy:
   "Report" → report
   "Presentation" → presentation
   "Article" → paper
   "Book Section" → paper
   "Dataset" → dataset
   (default) → report

4. Compare URLs against existing entries in llms-full.txt.
   Stage new entries in docs/staging/digital-promise.txt.
```

## Quirks

- The API silently caps `size` at 100. Requesting `size=200` returns 100 items and misreports `totalElements` as 100. Always use `size=100`.
- The `/server/api/core/items` endpoint (list all) returns 401 — only the discovery/search endpoint works anonymously.
- Sitemaps return HTTP 202 with empty bodies — broken/async. Do not rely on them.
- 19 collections exist (Artificial Intelligence, Learner Variability Project, Micro-credentials, etc.) — usable for topic filtering via `scope={collection-uuid}` param if needed.
