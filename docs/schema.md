# Learning Engineering Resource Hub — Schema

> All files in this repository must be UTF-8 (no BOM). `build_tags.py` rejects builds if mojibake is detected.

## Entry Metadata Fields

```yaml
title: string                    # Resource title as listed on AIMS Collaboratory
type: string                     # See types below
url: string                      # Direct URL to resource; AIMS page if direct URL not captured
url_confirmed: boolean           # true if URL was fetched and verified; false if inferred from scrape
doi: string|null                 # DOI for papers, if known
license: string|null             # License if stated (e.g. BSD-3-Clause, MIT, CC-BY, open-access)
source: string               # Producing organization or index source (e.g. "AIMS Collaboratory", "The Learning Agency", "Carnegie Mellon University", "CoSN")
date_added: date                 # When entry was added to this wiki
last_verified: date              # When source URL was last checked
description_inferred: boolean    # true = description derived from title/context; false = fetched directly
tags: list[string]               # Controlled vocabulary (see below)
```

## Resource Types

| Type | Description |
|---|---|
| `paper` | Peer-reviewed article, conference paper, or preprint |
| `report` | Research report, brief, or white paper |
| `code` | Source code repository |
| `framework` | Conceptual or methodological framework, guidance document |
| `platform` | Interactive tool, software platform, or web application |
| `tool` | Assessment instrument, diagnostic tool, rubric, or decision-support tool (not a full software platform) |
| `curriculum` | Instructional materials, lesson sequences, curriculum guides, or OER content |
| `blog-post` | Blog post or informal publication |
| `presentation` | Slide deck, poster, or video presentation |
| `project-website` | Website for a research project or initiative |
| `dataset` | Data resource or repository of learning interaction data |

## Tag Taxonomy

### Domain
`learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

### Method
`a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching` `computer-assisted-learning`
`automated-feedback` `qualitative-research` `meta-analysis` `longitudinal` `intelligent-tutoring`
`response-to-intervention`

### Topic
`student-belonging` `math-motivation` `pii-privacy` `data-sharing` `professional-development`
`formative-assessment` `digital-learning-platforms` `math-strategies` `personalized-learning`
`attendance` `prekindergarten` `math-word-problems` `genai-tutoring` `open-datasets` `ai-policy`
`ai-ethics` `inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness`
`dropout-prevention`

### Affiliation (producing organization)
`rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu` `northwestern-e4`
`norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments` `cosn`
`wwc` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm`
`lpi` `nap` `edtrust` `casel` `jla` `campbell-collaboration` `brookings`

## Tag Taxonomy Expansions (added during 2026-04-27 compilation)

The following tags were added beyond the initial set because the source material warranted them:
- `student-belonging` — RPPL belonging measurement work is a distinct research cluster
- `math-motivation` — Math Mind Measures and related LSU work
- `school-discipline` — Bahar & Auletto 2025 brief
- `english-learners` — Morales & Lepper 2024 brief
- `prekindergarten` — early childhood funding study
- Affiliation tags (`rppl`, `upgrade-platform`, `carnegie-learning`, `khan-academy`, `lsu`, `northwestern-e4`, `norc`, `lastinger-center`) — AIMS resources cluster strongly by producing organization; these tags make that structure queryable

## Notes on Provenance

### No-inference policy (established 2026-05-01)

Descriptions are **never** written from title alone. The following rules apply:

| Situation | Description | Flags |
|---|---|---|
| Page fetched, full content readable | Written from actual page content | `description_inferred: false`, `url_confirmed: true` |
| Page fetched, abstract only | Written from abstract | `description_inferred: true`, `url_confirmed: true` |
| PDF URL confirmed but content not extractable | Blank or publisher abstract only | `url_confirmed: true` |
| Page returns 404 / 403 / paywall | **Entry dropped** — not added to hub | N/A |
| Title only, no fetch possible | **Entry dropped** | N/A |

`description_inferred: true` means "summarized from fetched content, not validated against full source." It does **not** mean "guessed from title."

`url_confirmed: false` means the URL was not directly fetched and verified; the AIMS Collaboratory discovery page is used as fallback for older entries. New entries must have `url_confirmed: true`.

### Pre-2026-05-01 entries

Entries 1–74 were compiled under a looser standard: ~59 descriptions are `description_inferred: true` based on title + contextual signals, not confirmed page fetches. These should be re-audited and updated or dropped under the current policy during the next scrape pass.
