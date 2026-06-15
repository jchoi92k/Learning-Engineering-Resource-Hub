# Renaissance AI and Education Resource Hub — Backlog Indexing Prompt

Paste this verbatim (with the TARGET SOURCE filled in) when expanding coverage for a source
that already has some entries indexed but still has a large backlog.

---

## PROMPT START

You are expanding coverage for the **Renaissance AI and Education Resource Hub**.

**Target source:** `[INSERT SOURCE NAME EXACTLY AS IT APPEARS IN llms-full.txt]`
**Discovery URL:** `[INSERT DISCOVERY URL FROM data/source-targets.json]`

---

## Step 0 — Pre-flight checks

### 0a. Robots.txt / llms.txt

Before scraping, fetch the target source's `robots.txt` and `llms.txt`. Respect `Disallow` rules, `Crawl-delay`, and AI bot blocks. If restrictions have changed since the source's `.md` profile was written, stop and report. See `meta/agent-guide.md` "Robots.txt / llms.txt pre-check" for full policy.

### 0b. Read the source access matrix

Before fetching, find your target source's row in the **"Routine source access matrix"** at the top of `meta/source-audit.md`. That row tells you the access method (WebFetch / Playwright / manual), known gotchas (sitemap structure, JS rendering, pagination quirks), and whether the source is cloud-blocked.

You do **not** need to read the rest of `meta/source-audit.md` — only deeper sections if your source's row says "see notes" or behavior surprises you mid-run. You do **not** need to read `meta/sources-log.md`; it's archival, not action-relevant.

Also read `meta/inclusion-criteria.md`'s Level 2 (per-entry) rules — you'll apply them while staging.

If the matrix row says "Try Playwright," go straight to Playwright for this source. Don't waste fetches re-discovering documented failures.

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
Check `data/source-targets.json` for the known total and how many are already indexed
to understand how much backlog remains.

**Playwright fallback.** If WebFetch returns 403 or empty content for the listing or for individual pages — and the access matrix in `meta/source-audit.md` flags this source as "Try Playwright" or "Yes" — retry **once** with headless Chromium using the pattern in `meta/playwright-guide.md`. Cap at one retry per URL. See that guide for installation instructions (local vs. cloud).

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
#   Run: python scripts/build_from_db.py after merging.
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
- Suggested next step: which source to expand next (check `data/source-targets.json`
  for sources with `status: "active"` or `"new"` and lowest coverage pct)

## PROMPT END

---

## Source backlog reference (refreshed 2026-05-13)

Check `data/source-targets.json` for per-source totals and `docs/data.json`
(`meta.coverage`) for current indexed counts. Priority sources with largest backlogs:

| Source | Known Total | Indexed | Priority | Notes |
|---|---|---|---|---|
| What Works Clearinghouse (IRs) | 648 | ~178 | high | ~470 intervention reports remain. .gov bot detection may require Playwright from cloud. |
| Digital Promise | 252 | 254 | done | Use `scripts/playwright_scrape.py digital-promise` for re-runs. |
| Evidence for ESSA | ~300+ | 78 | high | Sitemap is non-chronological; secondary sitemaps (program-sitemap2.xml+) hold older entries. Skip "no studies met inclusion requirements" programs. |
| NWEA Research | 200+ | 70 | medium | Use `publication-sitemap.xml`. Not strictly chronological. |
| Mathematica | ~693 | 32 | medium | Coveo API via Playwright for full coverage; listing only sees partial. |
| WestEd | unknown | 14 | medium | Listing works; pagination may need exploration for older items. |
| UChicago Consortium | 319 | 31 | medium | Listing is paginated. |

## After each run

1. Check `docs/staging/` for the new `backlog-*.txt` file
2. Review entries (spot-check descriptions, tags, URLs)
3. Append to `docs/llms-full.txt` with correct numbering
4. Run `python scripts/build_from_db.py`
5. Delete the staging file
6. Commit when ready
