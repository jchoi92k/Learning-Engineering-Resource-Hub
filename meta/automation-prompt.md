# Renaissance AI and Education Resource Hub — Automation Prompt

Self-contained prompt for the weekly automated source-check. A cold-starting Claude Code session (interactive or routine) can execute it end-to-end without additional context: discovery → staging → merge → build → commit → push → PR.

For routine creation and configuration (`GH_TOKEN`, setup script, network access), see "Routine configuration" at the bottom of this file.

---

## PROMPT START

You are running the **weekly automated source-check** for the Renaissance AI and Education Resource Hub — a curated index of evidence-based K-12, higher-education, and learning-engineering resources.

**Your job:** Find new publications across the source list, stage them, merge into `docs/llms-full.txt`, rebuild derived files, append a run-log entry, commit, push, and open a pull request. Always open the PR — even if zero new entries were found — so the run is visible.

You are running headless. There is no human in the loop until the PR opens. Be conservative on judgment calls and surface everything in the PR body.

---

## Step 0 — Read the source access docs

Before doing any fetches, read these two files. They document what we already know about each source — known access patterns, sources that need Playwright, sources that 403 from the cloud, sources with non-chronological listings, sources we've explicitly decided to skip:

- `meta/source-audit.md` — start with the "**Routine source access matrix**" at the top. That table tells you, per source: whether WebFetch works from cloud sessions, whether Playwright is needed, and any source-specific gotchas.
- `meta/sources-log.md` — append-only log of attempts. Newest section at top is the most recent learning.

**Apply this knowledge.** If the matrix says a source needs Playwright, go straight to Playwright. Don't re-discover failures we've already documented.

---

## Step 1 — Load existing corpus and per-source recency

```python
import re
from collections import defaultdict

with open("docs/llms-full.txt", encoding="utf-8") as f:
    content = f.read()

existing_urls = set(re.findall(r'url: "([^"]+)"', content))
nums = list(map(int, re.findall(r"^### (\d+)\.", content, re.MULTILINE)))
next_entry_num = max(nums) + 1 if nums else 1
print(f"{len(existing_urls)} URLs indexed; next entry number: {next_entry_num}")
```

Capture `existing_urls` (a Python set, O(1) lookups) and `next_entry_num`. You will use both later.

---

## Step 2 — Check each source (with early-stop)

For each source below: fetch the discovery URL, extract candidate publication URLs in their displayed order, and walk through them applying the **early-stop heuristic**:

- Keep a `consecutive_dupes` counter, initialized to 0.
- For each candidate URL in displayed order:
  - If `url in existing_urls`: `consecutive_dupes += 1`. If `consecutive_dupes >= 3`, **stop scanning this source** and move to the next.
  - Else: add the URL to this source's `to_fetch` list and reset `consecutive_dupes` to 0.
- After the loop, fetch each URL in `to_fetch` and stage it (see Step 3).

The early-stop keeps the run cheap: for sources where the recent listings are already indexed, we do one listing fetch and skip ahead. For sources with accumulated new content, we fetch only the new pages.

**Playwright fallback (cloud session only).** If WebFetch returns 403 or empty/blank content for a source the access matrix in `meta/source-audit.md` flags as "Try Playwright" or "Yes" — or for a source the matrix says should work but doesn't on this run — retry **once** with headless Chromium:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    page = browser.new_page()
    page.goto(url, wait_until="networkidle", timeout=30000)
    html = page.content()
    browser.close()
# Parse `html` normally (regex or BeautifulSoup) to extract publication URLs or descriptions.
```

The `--no-sandbox` flag is required in the sandboxed cloud VM. Cap at one Playwright retry per URL — don't loop. If Playwright also fails, log it under non-critical failures and move on. After the run, append a line to `meta/sources-log.md` documenting what worked or didn't (Step 9).

### Source list

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
| NWEA Research | `https://www.nwea.org/publication-sitemap.xml` | `nwea.org/research/publication/[slug]/` |
| Mathematica | `https://mathematica.org/evidence?focusArea=Education&contentType=Publication` | `mathematica.org/publications/[slug]` |
| UChicago Consortium | `https://consortium.uchicago.edu/publications` | `consortium.uchicago.edu/publications/[slug]` |
| CREDO at Stanford | `https://credo.stanford.edu/research-reports/report-finder/` | `credo.stanford.edu/reports/item/[slug]/` |

**Source-specific notes:**

- **Brookings**: index only articles tagged with Brown Center on Education Policy. Skip Brookings Now news items, opinion pieces, and non-education content.
- **IES REL**: listings are JS-rendered, so the sitemap walk doesn't apply. Probe the 10 regional pages for recent IDs: `ies.ed.gov/ncee/rel/Products/Region/[region]/Publication/[id]`. Regions: `pacific`, `appalachia`, `central`, `mid-atlantic`, `midwest`, `northeast-and-islands`, `northwest`, `southeast`, `southwest`, `west`. Early-stop applies per region.
- **TNTP**: listing is JS-paginated (4 pages, 36 total). WebFetch only sees page 1 (10 items). Index what's reachable; note remaining pages in failures if relevant.
- **NWEA**: prefer the `publication-sitemap.xml` over the JS-rendered listing.
- **Mathematica**: listing is JS-rendered. WebFetch may see a partial set. If you find nothing via the listing, the Coveo search API at `mathematica.org/coveo/rest/search/v2` with filter `@mprhumanservicetopicsv2==Education` returns the full set, but it requires a bearer token intercept and is fragile — skip it for the routine, log as failure.
- **Sources to skip entirely**: Digital Promise (Playwright required), RAND (403 via WebFetch), MDRC (WAF blocks), AIMS Collaboratory (slow cadence — manual).

---

## Step 3 — Stage new entries

Write all new entries to `docs/staging/auto-YYYY-MM-DD.txt` (use today's UTC date).

**No-inference policy — strictly enforced:**
- Descriptions MUST come from fetched page content. Never from titles alone.
- If a page returns 404, 403, or has no readable content: drop it, log the failure, do not stage.
- `url_confirmed: true` only if the page was successfully fetched.

**Scope filter — you have authority to drop out-of-scope entries:**
This hub covers K-12 education, higher education, and learning engineering. Drop any entry whose primary subject is NOT education. Examples to drop: military/veteran welfare, adult disability employment (non-educational), cancer-survivor rehabilitation, agricultural extension, general labour market interventions with no school/campus component. Ask: "Is learning or teaching the central activity?" If no, drop it. Log dropped entries under "Dropped (out of scope)" in the staging header.

**Entry format:**

```
### N. Title of Resource

​```yaml
url: "https://exact-url"
type: report
source: "Organization Name"
url_confirmed: true
description_inferred: false
date_added: YYYY-MM-DD
tags: [tag1, tag2]
​```

2–3 sentence description from fetched page content.

---
```

Number entries from 1 in the staging file. Absolute numbers get assigned at merge time (Step 4).

**Tag taxonomy — use only these:**

Domain: `learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

Method: `a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching` `computer-assisted-learning` `automated-feedback` `qualitative-research` `meta-analysis` `longitudinal` `intelligent-tutoring` `response-to-intervention`

Topic: `student-belonging` `math-motivation` `pii-privacy` `data-sharing` `professional-development` `formative-assessment` `digital-learning-platforms` `math-strategies` `personalized-learning` `attendance` `prekindergarten` `math-word-problems` `genai-tutoring` `open-datasets` `ai-policy` `ai-ethics` `inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness` `dropout-prevention`

Affiliation: `wwc` `rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu` `northwestern-e4` `norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments` `cosn` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm` `lpi` `nap` `edtrust` `casel`

**Staging file header:**

```
# Staging: Automated source check
# Date: YYYY-MM-DD
# Sources checked: [list each source: "N new" / "0 new" / "FAILED: <reason>"]
# Dropped (out of scope): N
#   - <source>: "<title>" — <brief reason>
# Failures (non-critical): N
#   - <source>: <reason>
# Instructions (manual fallback): append to docs/llms-full.txt starting at entry [next_entry_num], run python docs/build_tags.py from docs/.
```

If zero new entries are found across all sources, still write the staging file with the header and a `# Result: 0 new entries.` line. The routine continues regardless.

---

## Step 4 — Merge staging into llms-full.txt

```python
import re

with open("docs/staging/auto-YYYY-MM-DD.txt", encoding="utf-8") as f:
    staging = f.read()

# Body starts at the first "### 1." (or "### N." if numbered differently)
match = re.search(r"\n### \d+\.", staging)
if match:
    body = staging[match.start():].lstrip("\n")
    entry_count = len(re.findall(r"^### \d+\.", body, re.MULTILINE))
else:
    body = ""
    entry_count = 0

if entry_count > 0:
    # Renumber from next_entry_num
    def renumber(m, start=[next_entry_num]):
        new_n = start[0]
        start[0] += 1
        return f"### {new_n}."
    renumbered = re.sub(r"^### \d+\.", renumber, body, flags=re.MULTILINE)

    with open("docs/llms-full.txt", "a", encoding="utf-8") as f:
        f.write("\n" + renumbered.rstrip() + "\n")
```

If `entry_count == 0`, skip the merge — `llms-full.txt` is unchanged.

---

## Step 5 — Rebuild derived files

```bash
cd docs && python build_tags.py
```

This regenerates `data.json`, `llms.txt`, `tags/*.md`, and `gem-knowledge.txt`. If it exits non-zero, **this is a CRITICAL failure** — record it and continue to Step 6 anyway (do not abort), so the PR still opens and the failure is visible.

---

## Step 6 — Append run summary to meta/automation-log.md

Append one block to the top of `meta/automation-log.md` (newest at top, immediately under the file header). Format:

```markdown
## YYYY-MM-DD

- **New entries:** N (entries M–(M+N-1)) — total now: T
- **Sources with new entries:** <source>: N, <source>: N, ...
- **Sources checked:** 14 total (`[list with new-count or 0 or FAILED]`)
- **Dropped (out of scope):** N
- **Failures (non-critical):** N
- **Critical failure:** NONE | <description>
- **Session:** https://claude.ai/code/${CLAUDE_CODE_REMOTE_SESSION_ID//cse_/session_}

---
```

Insert it under the file header so the most recent run is always near the top. This append guarantees a diff for every PR — even on zero-entry weeks.

---

## Step 7 — Commit, push, open PR

The cloud session has already placed you on a `claude/*` branch (auto-named). Don't create a new branch — work with the current one.

```bash
DATE=$(date -u +%Y-%m-%d)

# Clean up the staging file (gitignored, but explicit)
rm -f docs/staging/auto-$DATE.txt

git add docs/llms-full.txt docs/llms.txt docs/data.json docs/gem-knowledge.txt docs/tags/ meta/automation-log.md meta/sources-log.md
git commit -m "Weekly auto-update $DATE: N new entries from K sources"
git push -u origin HEAD
```

**Create the PR.** Try the agent's built-in GitHub tools first (PR creation works through them — confirmed in cloud sessions). If they don't expose PR creation, fall back to:

```bash
gh pr create \
  --base main \
  --head "$(git rev-parse --abbrev-ref HEAD)" \
  --title "Weekly auto-update $DATE: N new entries" \
  --body "$(cat <<'EOF'
## Weekly automation run

**Date:** YYYY-MM-DD UTC
**Session:** https://claude.ai/code/${CLAUDE_CODE_REMOTE_SESSION_ID//cse_/session_}

## Summary

- New entries: N (now total T)
- Sources with new entries: <list>
- Dropped (out of scope): N
- Non-critical failures: N
- Critical failure: NONE | <description>

## Source results

| Source | New | Notes |
|---|---|---|
| <source> | N | |
| <source> | 0 | already up to date |
| <source> | FAILED | <reason> |

## Dropped (out of scope)

- <source>: "<title>" — <brief reason>

## Non-critical failures

- <source>: <reason>

## Critical failure

NONE.

---

Generated by the weekly automation routine. Merge to apply.
EOF
)"
```

Substitute the actual values into the body before piping. If `gh` is missing or fails, log it as a critical failure in the run summary and surface in the session transcript — the branch is pushed, so the user can open the PR manually from GitHub.

---

## Failure handling — recap

**Non-critical** (continue; record under `Failures (non-critical)` in PR body):
- Source listing returns 403/404/timeout → skip that source.
- Individual page 403/404 or has no readable content → skip that entry.
- A source's URL pattern doesn't match what's actually on the page → skip, log.

**Critical** (still produce a PR; flag prominently in PR body):
- `build_tags.py` exits non-zero.
- `git push` fails.
- `gh pr create` fails (after fallback attempt).
- Any unhandled Python exception in the merge step.

For all critical failures, the PR (or session transcript if push fails) must clearly state what went wrong. Better to land a noisy PR than a silent failure.

---

## Step 8 — Print final summary

Print to the session transcript:
- New entries: N
- Sources with new entries: <list>
- Failures: <count> non-critical, <count> critical
- PR URL (or branch name if PR creation failed)

---

## Step 9 — Record access-method findings (only if new)

If this run revealed anything *new* about source access — a newly-broken URL, a newly-working workaround, a Playwright-required source that used to work via WebFetch, a sub-sitemap not yet documented — append a short dated block to the top of `meta/sources-log.md` (under the existing "## YYYY-MM-DD — First cloud routine run findings" template).

**Only append if the finding is new** (not already in `meta/source-audit.md`'s matrix or `meta/sources-log.md`'s existing entries). A run that hits the same 403s already documented does not need a new log entry — those are expected, recorded once, and don't need to accumulate.

If you appended a new finding, also stage `meta/sources-log.md` in your `git add` (Step 7).

If the finding contradicts the `meta/source-audit.md` matrix (e.g., a source the matrix says is fine started returning 403), still log it here. Do not edit `source-audit.md` mid-routine — flag it in the PR body and let the human update the matrix.

## PROMPT END

---

## Routine configuration

Create the routine at [claude.ai/code/routines](https://claude.ai/code/routines) (or via `/schedule` in the CLI, then complete config on the web). Settings:

- **Repository**: `jchoi92k/Learning-Engineering-Resource-Hub`
- **Prompt**: the content between `PROMPT START` and `PROMPT END` above
- **Model**: Sonnet 4.6 to start; bump to Opus 4.7 if quality drops
- **Schedule**: weekly, off-peak (e.g., Sunday 03:00 local) — user picks the actual time for first test
- **Branch push permission**: leave at default (`claude/`-prefixed only)
- **Network access**: **Full** (required to reach WWC, NWEA, Mathematica, WestEd, JEDM, etc. — they're not on the default Trusted allowlist)
- **Environment variables**:
  - `GH_TOKEN` — fine-grained PAT scoped to this repo with **Contents: Read & write** and **Pull requests: Read & write** permissions
- **Setup script** (one-time, cached after first run — ~2 min first time):
  ```bash
  #!/bin/bash
  apt update && apt install -y gh
  # Playwright (fallback for sources that 403 from cloud or are JS-rendered)
  pip install playwright
  npx -y playwright@latest install-deps chromium
  npx -y playwright@latest install chromium
  ```

  The Playwright install adds ~2 minutes to the first run but is cached by the environment, so subsequent runs start with Chromium already on disk. The `--no-sandbox` flag (used by the routine, not the install) handles sandboxing in the cloud VM.

**First test run:** click **Run now** on the routine detail page instead of waiting for the scheduled fire. Inspect the resulting PR closely; iterate the prompt before letting the weekly schedule run unattended.

**Updating the routine after prompt changes:** the routine stores a snapshot of the prompt at creation time. Edits to `meta/automation-prompt.md` in the repo do **not** propagate to the routine automatically. After editing the prompt in the repo, copy the new content between `PROMPT START` and `PROMPT END` and paste it into the routine's Instructions field on claude.ai/code/routines. Same for setup script changes — edit on the web side.

---

## After each run (manual review)

The PR is the review surface. To merge:
1. Open the PR on GitHub.
2. Skim the diff in `docs/llms-full.txt` and `meta/automation-log.md`.
3. Check the PR body's "Non-critical failures" and "Critical failure" sections.
4. Approve and merge. The branch can be auto-deleted if you've enabled that repo-wide.

If a critical failure shows up, open the session transcript via the link in the PR body to see what happened.
