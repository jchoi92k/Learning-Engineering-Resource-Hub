# Renaissance AI and Education Resource Hub — Schema

> All files in this repository must be UTF-8 (no BOM). `build_from_db.py` rejects builds if mojibake is detected.

## Entry Metadata Fields

```yaml
title: string                    # Resource title as listed by the source organization
type: string                     # See types below
url: string                      # Direct URL to resource
url_confirmed: boolean           # true if URL was fetched and verified; false if inferred from scrape
doi: string|null                 # DOI for papers, if known
license: string|null             # License if stated (e.g. BSD-3-Clause, MIT, CC-BY, open-access)
source: string               # Producing organization or index source (e.g. "What Works Clearinghouse", "Learning Policy Institute", "Digital Promise")
date_added: date                 # When entry was added to the hub
last_verified: date              # When source URL was last checked
description_inferred: boolean    # true = description derived from title/context; false = fetched directly
description_source: string|null  # What kind of text the description is — see "Description provenance" below
tags: list[string]               # Controlled vocabulary (see below)
```

`url` identifies a row: hub.db keeps one row per URL across published and excluded entries, compared case-insensitively and without a trailing slash (unique index `idx_entries_url_norm`; `build_from_db.py --check` reports any violation).

## Resource Types

| Type | Description |
|---|---|
| `paper` | Peer-reviewed article, conference paper, or preprint |
| `report` | Research report, brief, or white paper |
| `code` | Source code repository |
| `framework` | Conceptual or methodological framework, guidance document |
| `platform` | Interactive tool, software platform, or web application |
| `tool` | Assessment instrument, diagnostic tool, rubric, or decision-support tool (not a full software platform) |
| `curriculum` | Instructional materials, lesson sequences, curriculum guides, or OER content (reserved; no entries currently use it) |
| `review` | Evidence review or systematic review of an intervention or program |
| `article` | News article, magazine piece, or explainer from a source organization |
| `blog-post` | Blog post or informal publication |
| `presentation` | Slide deck, poster, or video presentation |
| `project-website` | Website for a research project or initiative |
| `dataset` | Data resource or repository of learning interaction data |

## Tag Taxonomy

### Domain
`learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

### Method
`a-b-testing` `automated-feedback` `coaching` `computer-assisted-learning` `genai`
`instructional-coaching` `intelligent-tutoring` `llm-application` `longitudinal`
`meta-analysis` `nlp` `qualitative-research` `rct` `response-to-intervention`

### Topic
`ai-ethics` `ai-policy` `attendance` `career-readiness` `cognitive-science` `college-access`
`data-sharing` `digital-learning-platforms` `dropout-prevention` `educational-systems-change`
`formative-assessment` `genai-tutoring` `inclusive-design` `math-motivation` `math-strategies`
`math-word-problems` `open-datasets` `personalized-learning` `pii-privacy` `prekindergarten`
`professional-development` `sel` `student-belonging` `writing-instruction`

### Affiliation (producing organization)
`aims` `assistments` `brookings` `campbell-collaboration` `carnegie-learning` `casel` `cast` `cmu-learnlab`
`cosn` `digital-promise` `duolingo` `edtrust` `iste-ascd` `jedm` `jla` `khan-academy` `lastinger-center` `lpi` `lsu`
`nap` `norc` `northwestern-e4` `rppl` `tla` `tools-competition` `unesco` `upgrade-platform`
`wpi` `wwc`

`jedm` / `jla` mark a small, selective set of methods papers from the Journal of Educational Data Mining and the Journal of Learning Analytics. These journals are not indexed systematically.

## Notes on Provenance

### No-inference policy

Descriptions are **never** written from title alone. The following rules apply:

| Situation | Description | Flags |
|---|---|---|
| Page fetched, full content readable | Written from actual page content | `description_inferred: false`, `url_confirmed: true` |
| Page fetched, abstract only | Written from abstract | `description_inferred: true`, `url_confirmed: true` |
| PDF URL confirmed but content not extractable | Blank or publisher abstract only | `url_confirmed: true` |
| Page returns 404 / 403 / paywall | **Entry dropped** — not added to hub | N/A |
| Title only, no fetch possible | **Entry dropped** | N/A |

`description_inferred: true` means "summarized from fetched content, not validated against full source." It does **not** mean "guessed from title."

`url_confirmed: false` means the URL was not directly fetched and verified. New entries must have `url_confirmed: true`.

### Description provenance (`description_source`)

| Value | Meaning |
|---|---|
| `listing` | Verbatim blurb from the source's listing page or API: every row the scripted pipeline inserts (June 2026 onward), plus the May 2026 Digital Promise rows, which are the DSpace API abstracts. A few early Evidence for ESSA rows are cut at 500 characters; the rest were restored to the full source text in August 2026. |
| `page-meta` | Verbatim one-sentence teaser from the item page's meta description (e.g. Brookings) |
| `page-abstract` | Verbatim abstract or opening text from the item page (e.g. NWEA, UChicago Consortium, CASEL `detail_fetch`; the May 2026 TNTP rows, restored to the full opening text in August 2026 except #683) |
| `llm-summary` | Written by an agent from the fetched page: the May 2026 hand-indexed entries (other than Digital Promise and TNTP), and weekly-run upgrades of `page-meta` teasers. Labels were checked against site text on a per-source sample in August 2026. |

### Database-only columns (not in the published files)

`data/hub.db` keeps two columns that the published outputs do not carry yet:

- `raw_item` — everything the scraper collected for the row, as staged (JSON): listing or API fields such as authors, date and the publisher's type label, evidence fields where a source provides them, and for detail-fetched pages the `page_meta` block (meta description, og:*, published time, canonical URL). Kept so later passes (tagging, type review, description upgrades) never need to fetch the page again. Rows inserted before 2026-08-31 have it only where a later re-scrape filled it.
- `source_subjects` — the publisher's own topic labels for the item (JSON list), unmapped to the hub's tag vocabulary.

Excluded rows with `exclude_reason = type_filtered:<label>` are items a source's `type_allow` filter set aside (for example Brookings commentary); they keep title, URL, blurb and `raw_item` and can be reactivated with `scripts/curate.py`. Rows with `source_on_hold` belong to a source whose weekly scraping is paused (Brookings); `out_of_scope` marks a row the review dropped under `docs/purpose.md` § Scope.
| `manual` | Written or edited by a maintainer |
| `null` | Not recorded |

`description_source` says what kind of text the description is. `description_inferred` keeps the meaning in the table above. New rows get the value from the staged item (`listing`, or the `detail_fetch` label); only `scripts/process_staged.py` and `scripts/curate.py` set it.
