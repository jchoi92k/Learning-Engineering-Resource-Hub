# WestEd

## Discovery

- **Method:** Server-rendered pagination (FacetWP)
- **Primary URL:** `https://www.wested.org/resources/library/?_paged={N}` (pages 1–140)
- **Alternative:** Two resource sitemaps exist (`resource-sitemap.xml`, `resource-sitemap2.xml`) but are hard to fetch directly
- **Pagination:** `_paged` URL param, 8-10 items per page, 140 pages
- **Total items:** ~1,254 (as of 2026-06-04)
- **Items per request:** 8-10

## Access

- **Rendering:** Server-rendered HTML (WordPress + FacetWP). No JS needed for content.
- **Playwright:** Not needed
- **robots.txt:** Very permissive. Only `/wp-admin/` blocked. Sitemaps declared.
- **llms.txt:** Not found
- **Rate limits:** None observed
- **WP REST API:** Locked (401 Unauthorized)

## Scope

- **Coverage strategy:** Index all resources
- **Current indexed:** 14
- **Estimated remaining:** ~1,240
- **Type filtering available:** `_resource_type=report` confirmed working. Types observed: Brief, Report, Guide, Paper, Tool, Research and Evaluation, Training and Professional Development, Case Study, Randomized Controlled Trial

## Entry metadata

**From listing page (`/resources/library/`):**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full, linked |
| URL | Yes | `/resource/{slug}/` |
| Type label | Yes | Resource type badge |
| Blurb | Yes | 1-2 sentences — usable |
| Thumbnail | Yes | Image |
| Date | No | Not on listing |
| Authors | No | Not on listing |

**From individual pages:**

| Field | Available | Quality |
|---|---|---|
| Title | Yes | Full |
| Description | Yes | Multi-paragraph, includes key findings |
| Authors | Yes | Named |
| Date/copyright | Yes | Year or full date |
| Focus areas | Yes | Topic tags (19 categories) |
| PDF link | Yes | S3-hosted (`wested2024.s3.us-west-1.amazonaws.com/...`) |
| Page count | Yes | Listed |
| Related resources | Yes | Linked |

**Description approach:** Listing blurbs are adequate for a 1-2 sentence description. Individual pages have much richer content if we want to upgrade quality.

## Scraping instructions

```
1. Paginate through the library:
   GET https://www.wested.org/resources/library/?_paged=1
   GET ...?_paged=2
   ...through _paged=140

2. From each page, extract all resource cards:
   - Title (link text)
   - URL (href, pattern: /resource/{slug}/)
   - Type label
   - Blurb (description text)

3. Compare URLs against existing entries in llms-full.txt

4. For new entries, the listing blurb is usually sufficient.
   If richer description needed, fetch individual page.

5. Stage new entries in docs/staging/wested.txt
```

## Quirks

- `/resources/` is a curated landing page, not a full listing. Use `/resources/library/` for the complete paginated list.
- `/resources/new-releases/` shows only the latest 9 items.
- FacetWP uses underscore-prefixed params (`_paged`, `_resource_type`). Standard `?page=` or `?type=` won't work.
- The discovery URL in `source-targets.json` (`?type=research-evaluation`) does NOT work — it uses the wrong param format. Should be updated to `/resources/library/` or `/resources/library/?_resource_type=report`.
- Focus areas (19 categories): AI, Assessment, Early Childhood, Economic Mobility, Education Choice, Education Finance, Educational Leadership, English Learner Services, Family Engagement, Infant/Toddler Care, Justice and Prevention, Learning and Technology, Literacy, Mathematics Education, Resilient and Healthy Schools, School and District Transformation, Science and Engineering Education, Special Education Policy, Teacher Workforce Support.
