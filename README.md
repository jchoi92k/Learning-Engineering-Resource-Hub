# Learning Engineering Resource Hub

A curated, agent-first referratory of 487+ evidence-based K-12 and higher education research resources — optimized for LLM consumption.

**[Browse →](https://jchoi92k.github.io/learning-engineering-resource-hub)** · Built and maintained with [Claude Code](https://claude.ai/code)

---

## For AI agents

Fetch the full index in a single request:

```
https://jchoi92k.github.io/learning-engineering-resource-hub/llms-full.txt
```

Or start with the discovery layer:

```
https://jchoi92k.github.io/learning-engineering-resource-hub/llms.txt
```

Each entry includes a URL, type, source, YAML metadata with tags, and a description written from fetched page content. A web UI for human browsing is at the GitHub Pages link above.

---

## What's in it

487 entries across reports, practice guides, papers, frameworks, and datasets from:

**Research & evidence** — What Works Clearinghouse (practice guides + intervention reports), Evidence for ESSA, Campbell Collaboration, IES Regional Education Labs, Brookings Institution

**Journals** — Journal of Educational Data Mining (JEDM), Journal of Learning Analytics (JLA)

**Policy & practice** — Learning Policy Institute, Education Trust, CASEL, National Academies Press

**Datasets** — NCES surveys, IEA international studies (TIMSS, PIRLS, PISA), CMU DataShop, OECD, ASSISTments, Duolingo, Stanford CEPA, and more

---

## Structure

```
docs/                 ← GitHub Pages source
  llms-full.txt       ← all entries, full YAML + descriptions (primary agent fetch target)
  llms.txt            ← discovery layer / entry point
  data.json           ← structured JSON consumed by the web UI
  index.html          ← human-facing search interface
  tags/               ← per-tag index files (generated)
  build_tags.py       ← regenerates data.json and tag files from llms-full.txt

meta/                 ← internal operational docs
  agent-guide.md      ← entry format, tag schema, source URL patterns, subagent protocol
  indexing-decisions.md ← editorial decision log
  sources-inventory.md  ← full source catalog with access notes
  llm-wiki-landscape.md ← architecture research and decisions
```

---

## Maintaining the hub

After adding or editing entries in `docs/llms-full.txt`, regenerate derived files:

```bash
cd docs
python build_tags.py
```

Then commit and push. See `meta/agent-guide.md` for entry format, tag taxonomy, source URL patterns, and the subagent protocol for parallel collection runs.

---

## Entry format

Each entry in `llms-full.txt` follows this structure:

```
### 488. Title of Resource

```yaml
url: "https://exact-url"
type: report
source: "Publishing Organization"
url_confirmed: true
description_inferred: false
date_added: 2026-05-04
tags: [tag1, tag2]
```

1–3 sentence description from fetched page content.

---
```

Types: `paper`, `report`, `framework`, `platform`, `code`, `dataset`, `blog-post`, `presentation`, `project-website`

---

## Tag taxonomy

**Domain** — `learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

**Method** — `rct` `meta-analysis` `longitudinal` `nlp` `llm-application` `intelligent-tutoring` `a-b-testing` `coaching` `qualitative-research` `response-to-intervention` + more

**Topic** — `formative-assessment` `personalized-learning` `sel` `professional-development` `open-datasets` `ai-policy` `college-access` `dropout-prevention` + more

Full vocabulary in `docs/schema.md`.

---

*Scope: all evidence-based K-12 and higher education — not limited to learning engineering. Sources are pre-curated organizations whose editorial judgment we trust.*
