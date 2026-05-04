# Learning Engineering Resource Hub — Agent Guide

> Read this first. Covers entry format, tag schema, source patterns, current state, and subagent protocol.
> Written for a cold-starting agent with no prior conversation context.

---

## What this is

A **referratory** — links + metadata, no content hosting — of evidence-based K-12 and higher education resources, optimized for LLM consumption via WebFetch. Single-file fetch at `docs/llms-full.txt` returns all entries. Human-facing UI at `docs/index.html` (GitHub Pages or local server).

**Scope**: All evidence-based K-12 and higher education. Not limited to learning engineering methods. Sources are pre-curated organizations whose editorial judgment we trust: WWC, LPI, EdTrust, NAP, CASEL, JEDM, Evidence for ESSA, etc.

---

## File layout

```
docs/
  llms-full.txt       # primary agent fetch target — all entries (THE authoritative file)
  llms.txt            # discovery layer / entry point for cold-arriving agents
  schema.md           # field definitions, type taxonomy, full tag vocabulary
  purpose.md          # scope and audience (partially stale — this guide is authoritative)
  build_tags.py       # parses llms-full.txt → data.json + tags/*.md
  data.json           # generated; consumed by index.html
  index.html          # human-facing UI (GitHub Pages or python -m http.server 8765)
  tags/               # generated per-tag markdown files
  staging/            # temporary staging area for subagent output (see protocol below)
meta/
  agent-guide.md              # THIS FILE — operational master reference
  sources-inventory.md        # full source catalog with access notes and URL patterns
  indexing-decisions.md       # log of every judgment call made during indexing
  inclusion-criteria.md       # what qualifies for inclusion (source-level + resource-level)
  comparable-repositories.md  # survey of comparable clearinghouses and their selection criteria
  sources-log.md              # raw access log for previously attempted sources
  source-audit.md             # systematic audit of source accessibility
```

---

## Current state

| Metric | Value |
|---|---|
| **Total entries** | 487 (as of 2026-05-03) |
| **Entry header** | `docs/llms-full.txt` line 9: `# Entries: 487` |
| **Next entry number** | 488 |

### Sources currently indexed

| Source | Entries | Count | Notes |
|---|---|---|---|
| What Works Clearinghouse — Practice Guides | 1–9, 21–39 | 29 | All accessible guides |
| What Works Clearinghouse — Intervention Reports | 40–137 | ~98 | ~481 of ~619 remaining |
| Learning Policy Institute (LPI) | 138–141, 149–174 | 30 | |
| National Academies Press (NAP) | 142–143 | 2 | How People Learn I & II |
| CASEL | 144 | 1 | SEL Framework |
| The Education Trust (EdTrust) | 145–148, 175–200 | 30 | |
| Evidence for ESSA | 201–229 | 29 | All Strong-rated program reviews |
| Journal of Educational Data Mining (JEDM) | 17, 230–258 | 30 | |
| Journal of Learning Analytics (JLA) | 259–283 | 25 | Vols 9–12, 2022–2025 |
| Campbell Collaboration | 284–308 | 25 | Education systematic reviews |
| Brookings Institution | 309–333 (3 gaps) | 22 | Brown Center on Education Policy; 3 news pieces removed |
| IES Regional Education Labs (REL) | 334–363 | 30 | All 10 REL regions |
| Digital Promise | 18–20, 364–390 | 30 | DSpace REST API + Playwright; 252 total items available |
| Datasets (initial batch) | 387–416 | 30 | CRDC, international assessments, learning eng datasets — see sources-inventory.md |
| NCES surveys (expansion) | 417–436 | 20 | NAAL, BTLS, CTE Stats, MGLS, SPP, NPSAS, B&B, SASS, PSS, SSOCS, HS&B, NLS-72, HST, EDSCLS, EDFIN, SLDS, Library Stats, IAP, Locale, CPS |
| IEA datasets | 437–440, 445–449 | 11 | ICCS, ICILS, TEDS-M, REDS + LaNA, TIMSS Advanced, TIMSS Longitudinal, CIVED, IELS |
| US Dept of Ed datasets | 441–442, 469–472 | 6 | College Scorecard, ESF COVID Relief, IDEA §618, NTEWS, Condition of Education, Digest of Ed Stats |
| Dataset survey expansion | 443–487 | 45 | ASSISTments (2), Duolingo (1), World Bank/ICPSR (3), CMU DataShop (10), OECD (5), Stanford CEPA/OI/NSC/Urban/NBER (15) |

### Known broken entries (do not fix without new URL)

| Entry | Issue |
|---|---|
| 14 (Carnegie Learning ESSA Math) | CDN PDF URL resolves to an Adobe Illustrator logo file from 2017, not a report |

### Pending work

No batches pending. Next expansion candidates:
- **WWC Intervention Reports** — ~481 remaining of 619 total; largest single opportunity
- **Digital Promise** — 252 total items; 30 indexed; 222 remaining across 19 collections
- **NAP** — 2 indexed; 3–6 more landmark reports identified
- **Duolingo Research** — not yet attempted
- **IEA datasets** — 6 indexed; realistic ceiling ~10–12; could add ICCS 2022, ICILS 2023, PIRLS Literacy
- **OECD datasets** — 3 indexed; realistic ceiling ~6–8; could add PISA for Dev, Ed at a Glance, TALIS Starting Strong
- **US Dept of Ed AI reports** — access failure 2026-05-03; tech.ed.gov redirected away, no discoverable listing page; PDFs accessible but binary (not parseable by WebFetch); retry requires browser navigation or direct PDF URLs
- **CCSSO AI guidance** — access failure 2026-05-03; resource-library slugs return 404; Drupal site but no clean listing page found; retry via browser or sitemap discovery

See `meta/sources-inventory.md` for full candidate list and access notes.

---

## Entry format

Every entry in `llms-full.txt` follows this exact format. The file uses `\n---\n` as the block separator.

```
### N. Title of Resource

```yaml
url: "https://exact-url-to-resource"
type: report
source: "Producing Organization Name"
url_confirmed: true
description_inferred: false
date_added: 2026-05-01
tags: [tag1, tag2, affiliation-tag]
```

1–3 sentence description written from actual fetched page content. Never from the title alone.

---
```

### Field values

| Field | Valid values | Notes |
|---|---|---|
| `type` | `paper`, `report`, `framework`, `platform`, `code`, `blog-post`, `presentation`, `project-website`, `dataset` | |
| `url_confirmed` | `true` / `false` | `true` = page was fetched and verified; `false` = URL inferred |
| `description_inferred` | `true` / `false` | `true` = summarized from fetched content; `false` = written from full readable page |
| `date_added` | ISO date | Use `2026-05-01` for entries added in this session |

---

## Source discipline rule

**Every source is a specific domain with a documented access pattern. Agents collect only what that domain has published.**

If a source's website is inaccessible, the agent writes a staging file with only a header explaining the failure — no entries. It does NOT go find third-party content attributed to or about that source from other websites.

Correct behavior when a source fails:
```
# Staging: Khan Academy
# Date: 2026-05-02
# ACCESS FAILURE: research.khanacademy.org redirects to homepage. No publications
# listing accessible via WebFetch. Recommend re-attempting via browser or finding
# an alternative URL. NO ENTRIES COLLECTED.
```

Wrong behavior: fetching ERIC/NBER/Google Scholar for papers *about* the source and attributing them to it.

The `source` field must always be the organization that published the content at the URL we're indexing — not the subject of the research.

---

## No-inference policy

**Descriptions must come from fetched page content. Never from titles alone.**

| Situation | Action |
|---|---|
| Page fetched, full content readable | Write description from content; `url_confirmed: true`, `description_inferred: false` |
| Page fetched, abstract/summary only | Write from abstract; `description_inferred: true` |
| 404 / 403 / paywall / connection refused | **Drop the entry** — do not add it |
| Title only, no fetch possible | **Drop the entry** |

If a description begins with "Published [date]." or "Panel: [names]." strip that metadata prefix — start from the actual substantive content.

---

## Tag taxonomy

Use only tags from this controlled vocabulary. Do not invent new tags without updating `schema.md` and `build_tags.py`.

**Domain**
`learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

**Method**
`a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching` `computer-assisted-learning` `automated-feedback` `qualitative-research` `meta-analysis` `longitudinal` `intelligent-tutoring` `response-to-intervention`

**Topic**
`student-belonging` `math-motivation` `pii-privacy` `data-sharing` `professional-development` `formative-assessment` `digital-learning-platforms` `math-strategies` `personalized-learning` `attendance` `prekindergarten` `math-word-problems` `genai-tutoring` `open-datasets` `ai-policy` `ai-ethics` `inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness` `dropout-prevention`

**Affiliation** (producing organization)
`rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu` `northwestern-e4` `norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments` `cosn` `wwc` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm` `lpi` `nap` `edtrust` `casel`

To add a new tag: add it to the correct category in `schema.md` AND to `TAG_CATEGORIES` in `build_tags.py`.

---

## Source URL patterns

### Active sources (confirmed working)

| Source | URL pattern | Discovery method |
|---|---|---|
| WWC Practice Guides | `https://ies.ed.gov/ncee/wwc/PracticeGuide/[N]` | Sequential N=1–30 |
| WWC Intervention Reports | `https://ies.ed.gov/ncee/wwc/InterventionReport/[ID]` | Sequential IDs; listing page is JS-rendered |
| LPI reports | `https://learningpolicyinstitute.org/product/[slug]` | Fetch topic pages first; slugs not predictable from titles |
| NAP reports | `https://www.nationalacademies.org/read/[ID]/chapter/` | Catalog IDs at `nap.nationalacademies.org` |
| EdTrust reports | `https://edtrust.org/resource/[slug]` | Fetch `edtrust.org/research/` listing; also `edtrust.org/rti/[slug]` pattern exists (see sources-inventory.md) |
| CASEL | `https://casel.org/fundamentals-of-sel/what-is-the-casel-framework/` | Direct URL |
| Evidence for ESSA | `https://evidenceforessa.org/program/[slug]` | Sitemap at `evidenceforessa.org/sitemap.xml` |
| JEDM papers | `https://jedm.educationaldatamining.org/index.php/JEDM/article/view/[ID]` | IDs not sequential; use volume/issue browse pages |
| JLA papers | `https://learning-analytics.info/index.php/JLA/article/view/[ID]` | IDs not sequential; use volume/issue browse pages |
| Campbell Collaboration | `https://campbellcollaboration.org/better-evidence/education-[slug].html` | Browse `/our-work/education/` listing; also try `/better-evidence/` search |
| Brookings (Brown Center) | `https://www.brookings.edu/articles/[slug]` | Sitemap at `brookings.edu/sitemap_index.xml`; curate manually from Brown Center listings |
| IES REL | `https://ies.ed.gov/ncee/rel/Products/Publication/[ID]` | Regional listing pages at `ies.ed.gov/ncee/rel/regions/[region]` |
| Digital Promise (DSpace) | `https://digitalpromise.dspacedirect.org/items/[UUID]` | REST API: `/server/api/discover/search/objects?scope=8b62a46e...&dsoType=item`; Playwright required to render |

### Known blocked sources

| Source | Status | Workaround |
|---|---|---|
| Digital Promise (DSpace via WebFetch) | Returns 202 + empty body (Angular SPA — JS not executed) | Use Playwright: `wait_for_selector('ds-item-page')` after `networkidle` |
| RAND | robots.txt returns 403 | Use Unpaywall with DOI to find OA versions |
| MDRC | WAF blocks automated requests | Use Unpaywall + DOI |
| Child Trends | Explicitly blocks Claude/Anthropic in robots.txt | Dead end |
| Carnegie Learning CDN | CDN PDF URLs serve marketing assets, not reports | Find reports via RAND/independent researchers |
| OECD (oecd.org) | WAF returns 403 on all sub-page fetches | Use WebSearch to get indexed snippets; set `url_confirmed: false` on any entries; descriptions from snippets are acceptable if substantive |

---

## Build pipeline

After modifying `llms-full.txt`:

1. Update the `# Entries: N` header on line 9 to the new count
2. From the `docs/` directory: `python build_tags.py`
3. This generates `data.json` (consumed by `index.html`), `tags/*.md`, and `tags/index.md`
4. Verify with `python -c "import json; d=json.load(open('data.json')); print(d['meta']['total'])`

To serve locally: run `python -m http.server 8765` from `docs/` — open `http://localhost:8765` in browser.

---

## Subagent protocol

**Problem**: Subagents that return collected entry data as text lose that data on context compaction. 110 entries were lost this way in a previous session.

**Rule: Any subagent collecting or generating entry data MUST write output to a file.**

### Staging workflow

1. Assign each collection subagent a staging file: `docs/staging/{source-name}.txt`
   - Example: `docs/staging/lpi.txt`, `docs/staging/jedm.txt`
2. The subagent writes formatted entry blocks to its staging file, numbered from 1 (not the final absolute number)
3. After all subagents complete, the main agent reads the staging files and appends to `llms-full.txt` with correct absolute numbering
4. Delete staging files after successful append

### Staging file format

```
# Staging: {Source Name}
# Date: 2026-05-01
# Final number range: 149–174 (assigned before run)

### 1. Title of First Entry

```yaml
url: "https://..."
type: report
source: "Source Name"
url_confirmed: true
description_inferred: false
date_added: 2026-05-01
tags: [tag1, tag2]
```

Description.

---

### 2. Title of Second Entry
...
```

### Subagent prompt template

When spawning a collection subagent, the prompt MUST include:
- The staging file path to write to (`docs/staging/{source}.txt`)
- The final number range assigned to this source
- The entry format (copy from this guide)
- The full tag taxonomy
- The no-inference policy
- The source URL pattern and discovery method
- Instruction: "Write ALL entries to the staging file as you confirm them. Do not return entry data as text."

---

## Adding new tags (checklist)

1. Add to `schema.md` under the correct category heading
2. Add to `TAG_CATEGORIES` dict in `build_tags.py`
3. If it's an affiliation tag, add to the Affiliation list in both files
4. Log the addition in `meta/indexing-decisions.md` with justification

---

## Hosting

**Public hosting:** GitHub Pages (chosen platform). Do not suggest Netlify, Vercel, or other cloud hosting.
- GitHub Pages: serves `docs/` directory from the repo root
- Local dev: `cd docs && python -m http.server 8765` → `http://localhost:8765`
- Demo: ngrok tunnel (session-only). Claude web UI confirmed working. ChatGPT unconfirmed.
- ngrok bypass header: `--request-header-add "ngrok-skip-browser-warning: true"`
