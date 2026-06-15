# Journal of Educational Data Mining (JEDM)

## Discovery

- **Method:** OAI-PMH protocol (single request, no pagination at current scale)
- **Endpoint:** `https://jedm.educationaldatamining.org/index.php/JEDM/oai?verb=ListRecords&metadataPrefix=oai_dc`
- **Total:** ~121 records (includes editorials and acknowledgements alongside research articles)
- **Platform:** Open Journal Systems (OJS) 3.4 by PKP
- **Date range:** Vol 1 No 1 (2009) through Vol 18 No 1 (2026)

## Access

- **robots.txt:** Only `/cache/` disallowed. No AI bot blocks. No crawl-delay.
- **llms.txt:** None (404).
- **Sitemap:** None (404).
- **Authentication:** None — fully open access.

## Scope

Peer-reviewed research on educational data mining: knowledge tracing, student modeling, learning analytics methods, automated assessment, feature engineering for learning data. Many special issues tied to annual EDM conferences.

## Entry metadata (from OAI-PMH oai_dc)

| Field | OAI key | Notes |
|-------|---------|-------|
| Title | `dc:title` | |
| Authors | `dc:creator` | One element per author |
| Abstract | `dc:description` | Full abstract |
| Date | `dc:date` | ISO format |
| DOI | `dc:identifier` | Zenodo DOIs (`10.5281/zenodo.NNNNNNN`) |
| URL | `dc:identifier` | Article page URL (filter for `article/view`) |
| Keywords | `dc:subject` | Multiple elements |
| PDF | `dc:relation` | Direct PDF URL |
| Language | `dc:language` | |

## Scraping instructions

**Single OAI-PMH request.** `ListRecords` with `metadataPrefix=oai_dc` returns all records with complete metadata (title, authors, abstract, keywords, DOI, date, PDF URL). No pagination needed at current scale (~121 records). For incremental updates, use the `from` parameter with a datestamp.

Filter out editorials and acknowledgements by checking `dc:title` — research articles have substantive titles; editorials are "Editorial Welcome", "Acknowledgements", etc.

## Quirks

- Article IDs are non-sequential (5, 6, 8, ... up to 1171) — OJS internal numbering includes drafts/deleted items
- Journal started in 2009 but OAI earliest datestamp is 2013 (records migrated to OJS later)
- All articles have Zenodo DOIs, not publisher DOIs
