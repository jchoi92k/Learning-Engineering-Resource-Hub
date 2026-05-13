# Renaissance AI and Education Resource Hub

A curated, agent-first referratory of 1,161+ evidence-based K-12, higher-education, and learning-engineering research resources — optimized for LLM consumption.

**[Browse →](https://jchoi92k.github.io/Learning-Engineering-Resource-Hub)** · Built and maintained with [Claude Code](https://claude.ai/code)

> New to the repo? Start with [`index.md`](index.md) for a full file map and common operations.

---

## For AI agents

Fetch the full index — all entries with descriptions, tags, and a navigation guide at the top:

```
https://jchoi92k.github.io/Learning-Engineering-Resource-Hub/llms-full.txt
```

An MCP server is also deployed at `https://renaissance-hub.joon-96a.workers.dev` for direct agent queries.

A web UI for human browsing is at the GitHub Pages link above.

---

## What's in it

1,161+ entries across reports, practice guides, papers, frameworks, and datasets from:

**Research & evidence** — What Works Clearinghouse (practice guides + intervention reports), Evidence for ESSA, Campbell Collaboration, IES Regional Education Labs, Brookings Institution, AIMS Collaboratory, NWEA, Mathematica, WestEd, UChicago Consortium, CREDO at Stanford

**Journals** — Journal of Educational Data Mining (JEDM), Journal of Learning Analytics (JLA)

**Policy & practice** — Learning Policy Institute, Education Trust, CASEL, National Academies Press, TNTP, Digital Promise

**Tools & platforms** — Tools Competition winners (K-12, post-secondary, datasets), LEVI Math teams (Carnegie Learning, Khan Academy, CMU, Eedi, Rising Academies, CU Boulder)

**Datasets** — NCES surveys, IEA international studies (TIMSS, PIRLS, PISA), CMU DataShop, OECD, ASSISTments, Duolingo, Stanford CEPA, and more

---

## Structure

```
index.md              ← start here: full repo map and common operations
CLAUDE.md             ← project instructions loaded by every Claude Code session

docs/                 ← GitHub Pages source (the published referatory)
  llms-full.txt       ← all entries with YAML + descriptions + auto-generated nav header
  llms.txt            ← compact index (titles, URLs, types, tags — no descriptions)
  data.json           ← structured JSON consumed by the web UI
  index.html          ← human-facing search interface
  tags/               ← per-tag index files (generated)
  build_tags.py       ← regenerates data.json and tag files from llms-full.txt
  schema.md           ← entry format, type taxonomy, full tag vocabulary
  purpose.md          ← scope, audience, hosting notes

meta/                 ← operational docs and tooling
  agent-guide.md      ← entry format, tag schema, source URL patterns, subagent protocol
  automation-prompt.md← self-contained prompt for weekly multi-source check
  backlog-prompt.md   ← self-contained prompt for backlog expansion on a single source
  inclusion-criteria.md
  sources-inventory.md
  source-audit.md, sources-log.md
  playwright-scrape.py, source-check.py
  source-targets.json

worker/               ← Cloudflare Worker (MCP server)
```

---

## Maintaining the hub

After adding or editing entries in `docs/llms-full.txt`, regenerate derived files:

```bash
cd docs
python build_tags.py
```

Then commit and push. See `meta/agent-guide.md` for entry format, tag taxonomy, source URL patterns, and the subagent protocol for parallel collection runs. See `index.md` for common operations.

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

Types: `paper`, `report`, `framework`, `platform`, `code`, `dataset`, `blog-post`, `presentation`, `project-website`, `review`

---

## Tag taxonomy

**Domain** — `learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

**Method** — `rct` `meta-analysis` `longitudinal` `nlp` `llm-application` `intelligent-tutoring` `a-b-testing` `coaching` `qualitative-research` `response-to-intervention` + more

**Topic** — `formative-assessment` `personalized-learning` `sel` `professional-development` `open-datasets` `ai-policy` `college-access` `dropout-prevention` + more

Full vocabulary in `docs/schema.md`.

---

*Scope: all evidence-based K-12 and higher education — not limited to learning engineering. Sources are pre-curated organizations whose editorial judgment we trust.*
