# Renaissance AI and Education Resource Hub — Automation Prompt

Paste this verbatim as the prompt when triggering an automated source-check run
(manually, via CronCreate, or via Task Scheduler). A cold-starting Claude Code
session with access to this repo can execute it without any additional context.

---

## PROMPT START

You are running an automated source-check for the **Renaissance AI and Education Resource Hub** — a curated index of evidence-based K-12 and higher education resources at `C:\Users\igisb\OneDrive\Documentos\TLA\Educational resources`.

**Your job:** Check each source below for new publications not already in the corpus. For every new entry you find, write it to the appropriate staging file. Do not return entry data as text — it will be lost. Write to files only.

---

## Step 1 — Load the existing corpus

Read `docs/llms-full.txt` and extract all URLs currently indexed. You will use this list to skip already-indexed entries.

```python
import re
with open("docs/llms-full.txt", encoding="utf-8") as f:
    content = f.read()
existing_urls = set(re.findall(r'url: "([^"]+)"', content))
```

---

## Step 2 — Check each source

For each source, fetch the discovery URL, extract all publication URLs from the page, filter out any already in `existing_urls`, then fetch and stage each new one.

### Source list with discovery URLs

| Source | Discovery URL | URL pattern for entries |
|---|---|---|
| Evidence for ESSA | `https://evidenceforessa.org/sitemap.xml` | `evidenceforessa.org/program/[slug]/` |
| JEDM | `https://jedm.educationaldatamining.org/index.php/JEDM/issue/archive` | `jedm.educationaldatamining.org/index.php/JEDM/article/view/[id]` |
| JLA | `https://learning-analytics.info/index.php/JLA/issue/archive` | `learning-analytics.info/index.php/JLA/article/view/[id]` |
| Campbell Collaboration | `https://www.campbellcollaboration.org/education/reviews/` | `campbellcollaboration.org/review/[slug]` |
| LPI | `https://learningpolicyinstitute.org/research/` | `learningpolicyinstitute.org/product/[slug]` |
| EdTrust | `https://edtrust.org/research/` | `edtrust.org/resource/[slug]` |
| Brookings (Brown Center only) | `https://www.brookings.edu/sitemap_index.xml` | `brookings.edu/articles/[slug]` |
| WWC Intervention Reports | `https://ies.ed.gov/ncee/wwc/Search/Products?productType=2` | `ies.ed.gov/ncee/wwc/InterventionReport/[id]` |
| WestEd | `https://wested.org/resources/?type=research-evaluation` | `wested.org/resource/[slug]/` |
| TNTP | `https://tntp.org/publications/` | `tntp.org/publication/[slug]/` |
| NWEA Research | `https://nwea.org/research/` | `nwea.org/research/publication/[slug]/` |
| Mathematica | `https://mathematica.org/evidence?focusArea=Education&contentType=Publication` | `mathematica.org/publications/[slug]` |
| UChicago Consortium | `https://consortium.uchicago.edu/publications` | `consortium.uchicago.edu/publications/[slug]` |
| CREDO at Stanford | `https://credo.stanford.edu/research-reports/report-finder/` | `credo.stanford.edu/reports/item/[slug]/` |

**For Brookings:** only index articles from the Brown Center on Education Policy. Skip opinion pieces, Brookings Now news items, and non-education content.

**For IES REL:** listing pages are JS-rendered — skip the listing. Instead, check for new publications by trying recent publication IDs on each of the 10 regional pages: `ies.ed.gov/ncee/rel/Products/Region/[region]/Publication/[id]`. Regions: pacific, appalachia, central, mid-atlantic, midwest, northeast-and-islands, northwest, southeast, southwest, west.

**For TNTP:** listing page is JS-paginated (4 pages, 36 total) — WebFetch only sees page 1 (30 items). Scrape individual publication URLs by slug if known; full listing requires Playwright. Index what's reachable, note remainder in the staging header.

**Skip entirely:** Digital Promise (Playwright required), RAND (403 via WebFetch), MDRC (WAF), AIMS (slow cadence — check manually).

---

## Step 3 — Stage new entries

Write new entries to `docs/staging/auto-[YYYY-MM-DD].txt`.

**No-inference policy — strictly enforced:**
- Descriptions MUST come from fetched page content. Never from titles alone.
- If a page returns 404, 403, or has no readable content: drop it, do not add.
- `url_confirmed: true` only if you successfully fetched the page.

**Entry format:**

```
### N. Title of Resource

```yaml
url: "https://exact-url"
type: report
source: "Organization Name"
url_confirmed: true
description_inferred: false
date_added: YYYY-MM-DD
tags: [tag1, tag2]
```

2–3 sentence description from fetched page content.

---
```

Number entries from 1 in the staging file (absolute numbers assigned at merge time).

**Tag taxonomy — use only these:**

Domain: `learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

Method: `a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching` `computer-assisted-learning` `automated-feedback` `qualitative-research` `meta-analysis` `longitudinal` `intelligent-tutoring` `response-to-intervention`

Topic: `student-belonging` `math-motivation` `pii-privacy` `data-sharing` `professional-development` `formative-assessment` `digital-learning-platforms` `math-strategies` `personalized-learning` `attendance` `prekindergarten` `math-word-problems` `genai-tutoring` `open-datasets` `ai-policy` `ai-ethics` `inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness` `dropout-prevention`

Affiliation: `wwc` `rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu` `northwestern-e4` `norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments` `cosn` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm` `lpi` `nap` `edtrust` `casel`

**Staging file header:**

```
# Staging: Automated source check
# Date: YYYY-MM-DD
# Sources checked: [list each source and how many new entries found, or "0 new"]
# Instructions: Review, then append to docs/llms-full.txt starting at entry [next number].
#   Run: python docs/build_tags.py from docs/ after merging.
```

---

## Step 4 — Write the staging file even if nothing is new

If no new entries are found across all sources, still write the staging file with the header and a summary line. This confirms the check ran.

```
# Staging: Automated source check
# Date: YYYY-MM-DD
# Sources checked: [all 14 sources above]
# Result: 0 new entries found. No action needed.
```

---

## Step 5 — Report

After writing the staging file, print a summary:
- Which sources were checked
- How many new entries found per source
- Any sources that failed to load (with error)
- Path to the staging file written

## PROMPT END

---

## How to trigger

**Manually (recommended for now):**
Open Claude Code in this repo and paste the prompt above.

**Via CronCreate (same subscription budget):**
Use `/schedule` in Claude Code or `CronCreate` tool with the prompt above and a weekly interval.

**Via Task Scheduler + Claude CLI:**
```bat
cd "C:\Users\igisb\OneDrive\Documentos\TLA\Educational resources"
claude -p "$(type meta\automation-prompt.md)"
```

Schedule this `.bat` file in Windows Task Scheduler for weekly execution.

---

## After each run

1. Check `docs/staging/` for new `auto-YYYY-MM-DD.txt` files
2. Review entries (spot-check descriptions, tags, URLs)
3. Append to `docs/llms-full.txt` with correct numbering
4. Run `python docs/build_tags.py`
5. Delete the staging file
6. Commit when ready
