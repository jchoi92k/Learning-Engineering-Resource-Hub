# Renaissance AI and Education Resource Hub — Agent Guide

> Read this first. Covers entry format, tag schema, source patterns, current state, and subagent protocol.
> Written for a cold-starting agent with no prior conversation context.

---

## What this is

A **referratory** — links + metadata, no content hosting — of evidence-based K-12 and higher education resources, optimized for LLM consumption via WebFetch. The primary file is `docs/llms-full.txt` — all entries with full descriptions and an auto-generated navigation header (tag directory, source/type summaries, usage instructions). A compact index without descriptions lives at `docs/llms.txt`. Human-facing UI at `docs/index.html` (GitHub Pages or local server).

**Scope**: All evidence-based K-12 and higher education. Not limited to learning engineering methods. Sources are pre-curated organizations whose editorial judgment we trust: WWC, LPI, EdTrust, NAP, CASEL, JEDM, Evidence for ESSA, etc.

---

## Read these before starting work

Don't start indexing without checking these first:

- **`sources/`** — per-source scraping profiles, JSON configs, and backlog files. **Read `sources/README.md` for conventions** (profile format, backlog format, fetch-failure handling, post-run sniff test). Read the relevant `{source}.md` profile before scraping a source. Profiles exist for: Digital Promise, TNTP, EdTrust, WestEd, NWEA Research, Brookings, WWC, LPI, UChicago Consortium, Evidence for ESSA, Mathematica.
- **`meta/source-audit.md`** — the "Routine source access matrix" at the top tells you, per source, whether WebFetch works, whether Playwright is needed, and any gotchas. Consult before fetching.
- **`meta/sources-log.md`** — append-only log of attempts. Most recent learnings at top.
- **`meta/inclusion-criteria.md`** — what qualifies for inclusion (source-level + resource-level rules).
- **`docs/schema.md`** — entry format and full tag vocabulary.

For workflow:
- **`meta/automation-prompt.md`** — the weekly all-source check. Runs as a cloud routine; also runnable interactively.
- **`meta/backlog-prompt.md`** — expanding coverage for a single source that already has entries.
- **`meta/automation-log.md`** — run-by-run log of weekly automated checks.
- **`meta/processing-log.md`** — auto-appended by `process_staged.py`; records every batch scraped and processed.

---

## File layout

```
docs/                          # published output only (GitHub Pages root)
  llms-full.txt               # primary file — all entries with descriptions + auto-generated nav header
  llms.txt                    # compact index (titles, URLs, types, tags — no descriptions)
  data.json                   # generated; consumed by index.html and MCP worker
  index.html                  # human-facing UI
  tags/                       # generated per-tag markdown files
  gem-knowledge.txt           # generated artifact for the Gemini Gem
  schema.md                   # field definitions, type taxonomy, full tag vocabulary
  purpose.md                  # scope and audience (public-facing summary)
  staging/                    # gitignored temp staging area for scraped data
scripts/                       # all Python tooling
  build_from_db.py            # rebuilds all published files from hub.db
  scrape.py                   # config-driven scraper (reads sources/*.json)
  process_staged.py           # processes staged JSON into hub.db
  verify_urls.py              # domain-aware URL verification
  source_check.py             # pre-flight source accessibility probe
  playwright_scrape.py        # scraper for JS-rendered sources (TNTP, Digital Promise)
sources/                       # per-source configs + profiles
  {source}.json               # machine-readable scraping config
  {source}.md                 # human-readable source profile
  {source}-backlog.txt        # items needing manual review
data/                          # database and data files
  hub.db                      # SQLite database — single source of truth
  source-targets.json         # coverage targets per source
  broken-urls.json            # known broken URLs from verify_urls.py
meta/                          # operational docs, prompts, guides, logs
  agent-guide.md              # THIS FILE — operational master reference
  automation-prompt.md        # self-contained prompt for the weekly cloud routine
  automation-log.md           # append-only log of weekly automated runs
  backlog-prompt.md           # self-contained prompt for backlog expansion
  sources-inventory.md        # full source catalog with access notes
  inclusion-criteria.md       # what qualifies for inclusion
  sources-log.md              # raw access log for source attempts
  source-audit.md             # accessibility audit + routine access matrix
  processing-log.md           # auto-appended by process_staged.py
  gem-instructions.md         # instructions for the Google Gemini Gem
  playwright-guide.md         # Playwright installation/usage reference
worker/                        # Cloudflare Worker (MCP server)
  src/, wrangler.toml         # imports docs/data.json at build time
private/                       # gitignored: strategy, meetings, decisions, research
  decisions.md                # append-only major-decisions log
  session-log.md              # append-only action log
  strategy/                   # positioning, briefs, design notes
  research/                   # landscape analysis, comparable repos
  meetings/                   # stakeholder notes (sensitive)
  write-ups/                  # drafts
  misc/                       # early scratch, legacy scripts (review for deletion)
```

---

## Current state

| Metric | Value |
|---|---|
| **Total entries** | 2,445 (as of 2026-06-15) |
| **Entry header** | Auto-generated by `build_from_db.py` |
| **Next entry number** | parsed at run time from hub.db — `SELECT MAX(num) FROM entries` + 1 |

### Where to find the live source list

This file no longer maintains a hand-curated per-source entry table — it drifted between 569 and 1,181 because every batch run had to remember to update it here. Instead:

- **Per-source indexed counts**: `docs/data.json`, `meta.coverage` array. Regenerated by `build_from_db.py`.
- **Per-source coverage targets** (known total, priority, status): `data/source-targets.json`.
- **Per-source access methods** (WebFetch ok? Playwright needed?): `meta/source-audit.md`'s "Routine source access matrix" at the top.
- **Per-source attempt history**: `meta/sources-log.md`.
- **Per-source scraping configs**: `sources/{source}.json` — machine-readable configs for `scripts/scrape.py`.
- **Processing history**: `meta/processing-log.md` — auto-appended by `process_staged.py`.

**Scraping pipeline** (preferred over manual agent scraping):
1. `python scripts/scrape.py {source}` — fetches listing data, outputs to `docs/staging/{source}.json` + backlog to `sources/{source}-backlog.txt`
2. `python scripts/process_staged.py {source}` — inserts entries into hub.db with auto-tagging, logs to `processing-log.md`
3. `python scripts/build_from_db.py` — rebuilds all published files (`llms-full.txt`, `llms.txt`, `data.json`, `tags/`, `gem-knowledge.txt`) from hub.db

scrape.py features: `url_filter` (filter API results by a listing page), `detail_fetch` (fetch individual pages for descriptions), path-based pagination, progress save/resume on interruption.

When a source's state materially changes (new source added, indexed count crosses a hundred-mark, access method changes), update the right canonical file — `source-targets.json` for coverage, `source-audit.md` for access, `sources-log.md` for attempt history — and let `docs/data.json` regenerate. Don't try to maintain a parallel table here.

### Known broken entries (do not fix without a new URL)

| Entry | Issue |
|---|---|
| 14 (Carnegie Learning ESSA Math) | CDN PDF URL resolves to an Adobe Illustrator logo file from 2017, not a report |

### Pending work / backlog

Major backlogs resolved (2026-06-15): WWC Tier -1 (1,088 excluded — no qualifying studies), ESSA No Evidence (1,134 excluded — empty descriptions), Mathematica no-description (97 excluded — no API summary or page content). Campbell filtered to education-only (52 active, 255 non-education excluded). JEDM/JLA removed (83 excluded — journals, not resource hubs).

Remaining: CASEL (~326 in progress), NAP (needs Playwright), IES REL (needs ERIC API config).

For known dead-end sources (RAND, MDRC, Child Trends WAF/robots blocks; CCSSO/US Dept of Ed structural 404s), see the "Known blocked sources" table later in this file and `meta/source-audit.md`.

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
| `date_added` | ISO date | Use today's date (ISO format: YYYY-MM-DD) |

---

## Robots.txt / llms.txt pre-check

**Before scraping any source, check its `robots.txt` and `llms.txt` first.** This applies to both automated pipeline runs and manual agent scraping.

1. Fetch `{domain}/robots.txt`. Respect `Disallow` rules for the paths you intend to crawl. If a `Crawl-delay` is specified, use it (scrape.py does this automatically via `check_robots()`). If the site blocks AI user-agents (e.g., AIMS blocks `GPTBot`, `anthropic-ai`), do not scrape — document the block in the source `.md` profile and stop.
2. Fetch `{domain}/llms.txt`. If it exists, check for any access restrictions or preferred interaction patterns. Note findings in the source `.md` profile.
3. Document both results in the source's `.md` profile under the Access section (`robots.txt: ...`, `llms.txt: ...`). This is already the convention — make sure it's done for every new source.

These checks are non-negotiable. A source that was open last month may have added restrictions since. Re-check on each new scraping session, not just the first time.

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

Use only tags from this controlled vocabulary. Do not invent new tags without updating `schema.md` and `build_from_db.py`.

**Domain**
`learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

**Method**
`a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching` `computer-assisted-learning` `automated-feedback` `qualitative-research` `meta-analysis` `longitudinal` `intelligent-tutoring` `response-to-intervention`

**Topic**
`student-belonging` `math-motivation` `pii-privacy` `data-sharing` `professional-development` `formative-assessment` `digital-learning-platforms` `math-strategies` `personalized-learning` `attendance` `prekindergarten` `math-word-problems` `genai-tutoring` `open-datasets` `ai-policy` `ai-ethics` `inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness` `dropout-prevention`

**Affiliation** (producing organization)
`rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu` `northwestern-e4` `norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments` `cosn` `wwc` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm` `lpi` `nap` `edtrust` `casel`

To add a new tag: add it to the correct category in `schema.md` AND to `TAG_CATEGORIES` in `build_from_db.py`.

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

## Encoding

**All files must be UTF-8 (no BOM).** `build_from_db.py` validates this at build time and will refuse to generate output if mojibake patterns are detected.

If mojibake is found: install `ftfy` (`pip install ftfy`) and run it on affected lines (titles and descriptions only — skip URL and YAML field lines). See the fix pattern used in the 2026-05-06 cleanup.

Common cause: saving through a process that re-encodes UTF-8 as CP1252 (old Notepad, Excel, non-UTF-8 terminals). Agents writing staging files should always use `encoding="utf-8"` explicitly.

---

## Build pipeline

After scraping and processing into hub.db:

1. From repo root: `python scripts/build_from_db.py`
2. The build reads all active entries from `data/hub.db` and generates:
   - `llms-full.txt` — all entries with descriptions and auto-generated nav header
   - `llms.txt` — compact index (no descriptions)
   - `data.json` — consumed by index.html, includes `meta.coverage` per-source counts
   - `tags/*.md` — per-tag markdown files
   - `gem-knowledge.txt` — artifact for the Gemini Gem
3. Verify with `python -c "import json; d=json.load(open('data.json', encoding='utf-8')); print(d['meta']['total'])"`

**Windows note:** Python on Windows defaults to cp1252, not UTF-8. Always pass `encoding='utf-8'` to `open()` in scripts and one-liners.

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
# Date: {today's date, YYYY-MM-DD}
# Final number range: 149–174 (assigned before run)

### 1. Title of First Entry

```yaml
url: "https://..."
type: report
source: "Source Name"
url_confirmed: true
description_inferred: false
date_added: {today's date, YYYY-MM-DD}
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
2. Add to `TAG_CATEGORIES` dict in `build_from_db.py`
3. If it's an affiliation tag, add to the Affiliation list in both files
4. Log the addition in `private/decisions.md` (append-only major-decisions log) with justification

---

## Hosting

**Public hosting:** GitHub Pages (chosen platform). Do not suggest Netlify, Vercel, or other cloud hosting.
- GitHub Pages: serves `docs/` directory from the repo root
- Local dev: `cd docs && python -m http.server 8765` → `http://localhost:8765`
- Demo: ngrok tunnel (session-only). Claude web UI confirmed working. ChatGPT unconfirmed.
- ngrok bypass header: `--request-header-add "ngrok-skip-browser-warning: true"`
