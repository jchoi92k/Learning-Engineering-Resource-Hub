# Renaissance AI and Education Resource Hub — Backlog Indexing Prompt

Paste this verbatim (with the TARGET SOURCE filled in) when expanding coverage for a source
that already has some entries indexed but still has a large backlog.

---

## PROMPT START

You are expanding coverage for the **Renaissance AI and Education Resource Hub**
at `C:\Users\igisb\OneDrive\Documentos\TLA\Educational resources`.

**Target source:** `[INSERT SOURCE NAME EXACTLY AS IT APPEARS IN llms-full.txt]`
**Discovery URL:** `[INSERT DISCOVERY URL FROM meta/source-targets.json]`

---

## Step 1 — Load existing corpus

Read `docs/llms-full.txt` and extract all URLs currently indexed so you can skip duplicates.

```python
import re
with open("docs/llms-full.txt", encoding="utf-8") as f:
    content = f.read()
existing_urls = set(re.findall(r'url: "([^"]+)"', content))
print(f"{len(existing_urls)} URLs already indexed")
```

Also count the current entry number ceiling (for staging file comments):

```python
nums = list(map(int, re.findall(r"^### (\d+)\.", content, re.MULTILINE)))
next_num = max(nums) + 1 if nums else 1
print(f"Next entry number will be: {next_num}")
```

---

## Step 2 — Discover new entries

Fetch the discovery URL for the target source. Extract all publication URLs matching
the source's URL pattern. Filter out any already in `existing_urls`.

Aim to collect **at least 30 new entries** (or all remaining if fewer than 30 exist).
Check `meta/source-targets.json` for the known total and how many are already indexed
to understand how much backlog remains.

**No-inference policy — strictly enforced:**
- Fetch each publication page before writing its entry.
- Description MUST come from fetched page content. Never from the title alone.
- If a page returns 404, 403, or has no readable content: drop it, do not add.
- `url_confirmed: true` only if you successfully fetched the page.

**Scope filter — you have authority to drop out-of-scope entries:**
This hub covers K-12 education, higher education, and learning engineering. Drop any entry whose primary subject is NOT education, even if it appears on the source's listing page. Examples of what to drop: military/veteran welfare, adult disability employment (non-educational), cancer survivor rehabilitation, agricultural extension, general labour market interventions with no school or campus component. Ask: "Is learning or teaching the central activity?" If no, drop it. Log dropped entries in the staging file header as "Dropped (out of scope): N — [brief reason]".

---

## Step 3 — Stage new entries

Write all new entries to `docs/staging/backlog-[source-slug]-[YYYY-MM-DD].txt`.

Number entries from 1 in the staging file (absolute numbers assigned at merge time).

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

**Staging file header:**

```
# Staging: Backlog expansion — [Source Name]
# Date: YYYY-MM-DD
# Discovery URL: [url]
# Entries found: N new (skipped M already indexed)
# Instructions: Review, then append to docs/llms-full.txt starting at entry [next_num].
#   Run: python docs/build_tags.py from docs/ after merging.
```

**Tag taxonomy — use only these:**

Domain: `learning-engineering` `math-education` `literacy` `k-12` `early-childhood`
`english-learners` `higher-ed` `school-discipline`

Method: `a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching`
`computer-assisted-learning` `automated-feedback` `qualitative-research`
`meta-analysis` `longitudinal` `intelligent-tutoring` `response-to-intervention`

Topic: `student-belonging` `math-motivation` `pii-privacy` `data-sharing`
`professional-development` `formative-assessment` `digital-learning-platforms`
`math-strategies` `personalized-learning` `attendance` `prekindergarten`
`math-word-problems` `genai-tutoring` `open-datasets` `ai-policy` `ai-ethics`
`inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness`
`dropout-prevention`

Affiliation: `wwc` `rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu`
`northwestern-e4` `norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments`
`cosn` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm` `lpi` `nap`
`edtrust` `casel`

---

## Step 4 — Write the staging file even if nothing new is found

```
# Staging: Backlog expansion — [Source Name]
# Date: YYYY-MM-DD
# Result: 0 new entries found. All known publications may already be indexed, or
#         the discovery page was unreachable.
```

---

## Step 5 — Report

Print a summary:
- How many new entries were found and staged
- How many were skipped (already indexed)
- Any pages that failed to load
- Path to the staging file written
- Suggested next step: which source to expand next (check `meta/source-targets.json`
  for sources with `status: "active"` or `"new"` and lowest coverage pct)

## PROMPT END

---

## Source backlog reference

Check `meta/source-targets.json` for per-source totals and `docs/data.json`
(`meta.coverage`) for current indexed counts. Priority sources with largest backlogs:

| Source | Known Total | Priority | Notes |
|---|---|---|---|
| What Works Clearinghouse | 648 | high | 471+ intervention reports remaining |
| Digital Promise | 252 | high | Playwright only — manual batches |
| UChicago Consortium | 319 | high | Not yet indexed |
| Evidence for ESSA | unknown | high | Promising + Demonstrates a Rationale tiers remain |
| NWEA | 200+ | medium | Not yet indexed |
| Mathematica | unknown | medium | Not yet indexed |
| WestEd | unknown | medium | Not yet indexed |

## After each run

1. Check `docs/staging/` for the new `backlog-*.txt` file
2. Review entries (spot-check descriptions, tags, URLs)
3. Append to `docs/llms-full.txt` with correct numbering
4. Run `python docs/build_tags.py`
5. Delete the staging file
6. Commit when ready
