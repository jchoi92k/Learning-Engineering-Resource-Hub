# Frontiers in Education

## Discovery

- **Method:** Frontiers search API, `POST https://www.frontiersin.org/api/v3/journals/search/articles` (the endpoint the journal's own listing pages call). Body: `Filter.JournalId` 1239, `Filter.SectionId` (STEM Education 1370, Teacher Education 1362, Higher Education 1946; 0 for all), `Filter.Sort` 3 = most cited, `StartDate` / `EndDate`, or `ArticleIds` for a fixed list.
- **Listing pages:** `https://www.frontiersin.org/journals/education/articles` and `/journals/education/sections/{slug}/articles?sort=Most%20cited`, server-rendered; the sort and filters call the API above.
- **Total:** 8,733 articles in the journal (listing count, 2026-10-14). Since 2021: STEM Education 904, Teacher Education 1,056, Higher Education 1,680 (API `totalCount`, 2026-10-27).
- **Sitemaps:** publisher-wide (`/articles/sitemap-index.xml`, 205 child sitemaps), not split by journal; not used.

## Access

- **robots.txt:** `Allow: /`; disallows `/images/`, `/production/`, `/review/`, `/mail/`, `/admin/`. No crawl-delay, no AI user-agent blocks (2026-10-14).
- **llms.txt:** Present. Gives URL patterns, asks for canonical `/journals/{journal}/articles/{doi}/full` pages, citation with title, journal, date and DOI, and respect for robots.txt and rate limits.
- **Terms of use:** https://www.frontiersin.org/legal/terms-and-conditions ("come into effect on 16th December, 2020"; JS-rendered, read via Playwright 2026-10-14). §14: text and data mining of public content "permitted for the legitimate purpose of enrichment of external collections of scientific literature", subject to restriction if it hinders site performance. §7: articles including abstracts are CC BY unless stated otherwise; listed article metadata is CC0. §9: registered users may link from "respectable websites". Text saved under `private/research/licensing-2026/terms/`.
- **Authentication:** None; fully open access.

## Scope

Frontiers in Education is a peer-reviewed open-access journal (handling editor and reviewers named on each article). The hub holds a one-time selected set (issue #7, 2026-10-27), not systematic coverage: the requested articles plus the most-cited research articles published since 2021 in STEM Education, Teacher Education and Higher Education. Research article types: Original Research, Systematic Review, Review, Brief Research Report, Mini Review, Methods. Perspective, Opinion, Hypothesis and Theory, Conceptual Analysis and Editorial are out of genre.

## Entry metadata

**From the API:**
| Field | Available | Notes |
|-------|-----------|-------|
| Title | Yes | `title` |
| URL | Yes | built from `doi`: `/journals/education/articles/{doi}/full` |
| Abstract | Yes | `abstract`, full text; used as the description (`listing`) |
| Type | Yes | `articleType.name` |
| Authors | Partly | `authors[].fullName` in filtered queries; **absent when queried by `ArticleIds`** |
| Citations, views | Yes | `impact.citations.count`, used only for selection |

**From article pages (server-rendered `citation_*` tags):**
| Field | Available | Notes |
|-------|-----------|-------|
| Publication date | Yes | `citation_publication_date` (`YYYY/MM/DD`) |
| Authors | Yes | `citation_author` ("Last, First") |
| PDF | Yes | `citation_pdf_url` → `document_url` |
| Licence | Yes | Body text: "distributed under the terms of the Creative Commons Attribution License (CC BY)", linking CC BY 4.0 |

## Scraping instructions

`python scripts/scrape.py frontiers-education` with `sources/frontiers-education.json`: one API request with the fixed `ArticleIds`, then `detail_fetch` (`fetch_all`) reads each article page once at 12 s spacing for date, authors and PDF link. `process_staged.py` sets `license` = `CC BY 4.0` from the config; the build adds the attribution line. To add requested articles later, append their article IDs (the number after `feduc.YYYY.` in the DOI) and rerun; the diff skips rows already indexed.

## Quirks

- The API's `publishedDate` ("21 Feb 2025") is not parsed by `_norm_date`; the page's `citation_publication_date` supplies the date.
- Some publisher abstracts carry artefacts: #9074 has manuscript line numbers inside the text, #9066 has fused section headings ("IntroductionEmbodied learning").
- `detail_fetch` page text on these pages is journal banner text, not the article; descriptions come from the API abstract.
- Research Topics can span journals: "Education in Synthetic Biology" (52932) is hosted by Frontiers in Bioengineering and Biotechnology, with 4 of its 10 articles in Frontiers in Education.
