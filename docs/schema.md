# Learning Engineering Resource Hub — Schema

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
`aims` `assistments` `campbell-collaboration` `carnegie-learning` `casel` `cmu-learnlab`
`digital-promise` `duolingo` `edtrust` `khan-academy` `lastinger-center` `lpi` `lsu`
`nap` `norc` `northwestern-e4` `rppl` `tla` `tools-competition` `upgrade-platform`
`wpi` `wwc`

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
