# Renaissance AI and Education Resource Hub — New Source Onboarding Prompt

Self-contained prompt for **adding a brand-new source** to the hub. Use when the source isn't in the corpus yet and isn't on the weekly routine's source list.

- For sources already partially indexed → use `meta/backlog-prompt.md`.
- For the recurring weekly check across known sources → use `meta/automation-prompt.md`.

Designed for interactive use (paste into a Claude Code session, fill in the inputs, run). Can also be invoked headlessly as a one-off routine; the prompt is fully self-contained either way.

The output is always a pull request — never auto-merge. Adding a source is a judgment-laden decision; a human reviews before it lands.

---

## Inputs (fill these in before running)

```
SOURCE_NAME:        # e.g. "NWEA Research"
HOMEPAGE_URL:       # e.g. "https://www.nwea.org/research/"
EXAMPLE_PUB_URL:    # an individual publication URL from this source, for pattern discovery
INITIAL_PASS_SIZE:  # default 30. Cap at ~50; use backlog-prompt.md for larger batches afterward.
PRIORITY:           # high | medium | low (maintainer's guess; can be revised)
LINKED_ISSUE:       # GitHub issue number that suggested this source, or "none"
```

---

## PROMPT START

You are onboarding a new source to the **Renaissance AI and Education Resource Hub**.

**Your job:** Confirm scope, discover the access method, stage an initial pass of entries, update the canonical source documentation, and open a PR. The PR is the review surface — do not merge.

You are running with the inputs at the top of this file. Apply them throughout.

---

## Step 0 — Read access docs and inclusion criteria

Before fetching anything, read these:

- `meta/source-audit.md` — the "Routine source access matrix" at the top documents access methods for sources we already index. Look for analogous sources (e.g., if you're adding another OJS journal, JEDM/JLA's rows are informative).
- `meta/sources-log.md` — most recent attempt log entries at top. May contain notes on related sources or domains.
- `meta/inclusion-criteria.md` — Level 1 (source-level) and Level 2 (resource-level) inclusion criteria. **You will apply Level 1 in Step 1.**
- `meta/sources-inventory.md` — confirm the source isn't already cataloged under a different name.

---

## Step 1 — Re-confirm scope (Level 1 inclusion check)

Apply `meta/inclusion-criteria.md`'s **Level 1 source criteria**. The source qualifies if it meets all three:

1. **Editorial accountability** — documented review/selection process (peer review, expert panel, evidence standards). Self-published vendor content does not qualify.
2. **Public access** — content freely accessible (HTML, OA PDF). Paywalled-only is excluded.
3. **Relevance** — publishes research, evidence syntheses, frameworks, or tools directly relevant to K-12 / higher-ed / learning systems.

If the source fails any criterion: **abort.** Open a PR (Step 9) whose body says `OUT OF SCOPE: <criterion> — <reason>`, with no entry changes. Do not proceed to Step 2.

If the source passes: continue.

---

## Step 2 — Discover the access method

Try these in order. Stop at the first one that yields a usable list of publication URLs:

1. **Sitemap** — try `HOMEPAGE_URL/sitemap.xml`, `HOMEPAGE_URL/sitemap_index.xml`, `HOMEPAGE_URL/publication-sitemap.xml`, `HOMEPAGE_URL/post-sitemap.xml`. Sitemaps are the gold standard — structured, exhaustive, no JS.
2. **Listing page** — look for `/publications`, `/research`, `/reports`, `/our-work`, or similar. Fetch with WebFetch. If empty or near-empty, the listing is likely JS-rendered → fall back to step 5.
3. **RSS / Atom feed** — try `/feed`, `/feed.xml`, `/rss`, `/atom.xml`. Less common but cheap to check.
4. **API endpoint** — look for OPDS, DSpace REST, Coveo, GraphQL, JSON-LD hints in page headers or robots.txt. Document any API endpoint found.
5. **Playwright fallback** — if WebFetch returns 403 or empty for the listing, retry once with headless Chromium:

   ```python
   from playwright.sync_api import sync_playwright

   with sync_playwright() as p:
       browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
       page = browser.new_page()
       page.goto(HOMEPAGE_URL, wait_until="networkidle", timeout=30000)
       html = page.content()
       browser.close()
   ```

6. **All methods failed** — document this in Step 6 (the source-audit row says "manual / no auto-access") and Step 9's PR body. Skip Steps 4–5 (no initial pass possible). Still register the source in the canonical files so it shows up in our inventory.

**Record what worked:** the access method becomes the row you'll add to `meta/source-audit.md`'s matrix in Step 6.

---

## Step 3 — Identify the URL pattern for individual publications

From the listing/sitemap, extract 3–5 example publication URLs and infer the pattern:

- `evidenceforessa.org/program/[slug]/` (slug-based, single segment)
- `jedm.educationaldatamining.org/index.php/JEDM/article/view/[id]` (numeric ID)
- `mathematica.org/publications/[slug]` (slug-based)
- `nwea.org/research/publication/[slug]/` (slug-based, nested path)

Verify the pattern matches `EXAMPLE_PUB_URL`. If it doesn't, you've found the wrong pattern — re-examine and try again. If you can't find a stable pattern, record this as a problem in Step 6 (source needs manual handling).

---

## Step 4 — Estimate known total

A rough count of total publications, used for `meta/source-targets.json`'s `known_total` field. Methods:

- From sitemap: `len(re.findall(r"<loc>([^<]+)</loc>", sitemap_text))` filtered by URL pattern.
- From listing: paginate and count, or read a "showing N of M" indicator if present.
- Conservative ranges are fine: `"200+"` or `"unknown"` are both acceptable if you can't get a clean count.

---

## Step 5 — Initial pass: stage entries

Load existing URLs to skip duplicates (rare for a brand-new source, but possible if there's overlap):

```python
import re
with open("docs/llms-full.txt", encoding="utf-8") as f:
    content = f.read()
existing_urls = set(re.findall(r'url: "([^"]+)"', content))
nums = list(map(int, re.findall(r"^### (\d+)\.", content, re.MULTILINE)))
next_entry_num = max(nums) + 1 if nums else 1
```

Iterate publication URLs in the source's natural order (chronological if available). Walk up to `INITIAL_PASS_SIZE`:

- Skip URLs already in `existing_urls`.
- Fetch each candidate. Apply the **no-inference policy**: description must come from fetched page content. If 403 / 404 / empty, drop and log.
- Apply the **scope filter**: drop entries whose primary subject isn't education (`meta/inclusion-criteria.md`'s scope section is the reference).
- Use Playwright fallback if a page consistently 403s on WebFetch.

Stage all confirmed entries to `docs/staging/new-source-{slug}-YYYY-MM-DD.txt` (where `{slug}` is a lowercase kebab-case version of `SOURCE_NAME`).

**Staging file header:**

```
# Staging: New source onboarding — [SOURCE_NAME]
# Date: YYYY-MM-DD
# Discovery URL: [HOMEPAGE_URL]
# Access method: [sitemap | listing | API | Playwright | failed]
# URL pattern: [pattern]
# Estimated total: [number or range]
# Entries staged: N (of INITIAL_PASS_SIZE attempted)
# Dropped (out of scope): N
# Failures (non-critical): N
```

**Entry format** — same as the rest of the corpus:

```
### M. Title of Resource

​```yaml
url: "https://exact-url"
type: report
source: "[SOURCE_NAME exactly]"
url_confirmed: true
description_inferred: false
date_added: YYYY-MM-DD
tags: [tag1, tag2]
​```

2–3 sentence description from fetched page content.

---
```

Numbering starts at 1 in the staging file; absolute numbers are assigned in Step 7.

**Tag taxonomy** (use only these — same as the other prompts):

Domain: `learning-engineering` `math-education` `literacy` `k-12` `early-childhood` `english-learners` `higher-ed` `school-discipline`

Method: `a-b-testing` `rct` `nlp` `llm-application` `genai` `coaching` `computer-assisted-learning` `automated-feedback` `qualitative-research` `meta-analysis` `longitudinal` `intelligent-tutoring` `response-to-intervention`

Topic: `student-belonging` `math-motivation` `pii-privacy` `data-sharing` `professional-development` `formative-assessment` `digital-learning-platforms` `math-strategies` `personalized-learning` `attendance` `prekindergarten` `math-word-problems` `genai-tutoring` `open-datasets` `ai-policy` `ai-ethics` `inclusive-design` `sel` `writing-instruction` `college-access` `career-readiness` `dropout-prevention`

Affiliation: `wwc` `rppl` `upgrade-platform` `carnegie-learning` `khan-academy` `lsu` `northwestern-e4` `norc` `lastinger-center` `aims` `tla` `cmu-learnlab` `assistments` `cosn` `unesco` `cast` `iste-ascd` `digital-promise` `duolingo` `jedm` `lpi` `nap` `edtrust` `casel`

If the new source warrants its own affiliation tag (an organization with multiple existing or planned entries), propose adding one — but do **not** add it in this PR. Flag it in the PR body for separate consideration; affiliation tag additions follow the checklist in `meta/agent-guide.md` ("Adding new tags").

---

## Step 6 — Update canonical source docs

Five files get updated. All five edits go into the same PR.

### 6a. `meta/source-targets.json` — coverage tracking

Add an entry:

```json
"SOURCE_NAME": {
  "discovery_url": "...",
  "url_pattern": "...",
  "access_method": "sitemap | listing | api | playwright | manual",
  "known_total": <number or "unknown">,
  "priority": "[PRIORITY]",
  "status": "active",
  "notes": "<1-line, e.g. 'Sitemap non-chronological — early-stop heuristic less effective'>"
}
```

### 6b. `meta/sources-inventory.md` — catalog entry

Add a section under the right category (Research & evidence / Journals / Policy & practice / etc.) with:

```markdown
**[SOURCE_NAME]**
- URL: [HOMEPAGE_URL]
- What it is: <1–2 sentences>
- Why pre-curated: <editorial process / funder / peer review>
- Content types: `[type]`
- Access: ✅ Confirmed — [method]. URL pattern: `[pattern]`
- **Indexed:** N entries (initial pass). Known total: [number or "unknown"].
- Scale: <current coverage / what's remaining>
```

### 6c. `meta/source-audit.md` — access matrix row

Add a row to the "Routine source access matrix" table near the top:

```
| [SOURCE_NAME] | [discovery URL] | ✅/❌/⚠️ | ✅/❌/⚠️ | No/Yes/Try | <gotchas>  |
```

Columns are: Source, Discovery URL, WebFetch (local), WebFetch (cloud), Playwright needed?, Notes.

### 6d. `meta/sources-log.md` — attempt log

Append a row to the most recent dated section (or create today's section if needed):

```
| [SOURCE_NAME] | [HOMEPAGE_URL] | Yes/Partial/No | Research org | High/Medium/Low | <notes incl. access method> | <entry range> | YYYY-MM-DD |
```

### 6e. `meta/automation-prompt.md` — add to the weekly routine's source list

Add the source as a row to the source list table in Step 2 of `automation-prompt.md`. After this PR merges, **the routine running on claude.ai/code/routines also needs its Instructions field updated to include the new source** — flag this clearly in the PR body so the maintainer doesn't forget.

---

## Step 7 — Merge staging into llms-full.txt

```python
import re

with open("docs/staging/new-source-{slug}-YYYY-MM-DD.txt", encoding="utf-8") as f:
    staging = f.read()

match = re.search(r"\n### \d+\.", staging)
if match:
    body = staging[match.start():].lstrip("\n")
    entry_count = len(re.findall(r"^### \d+\.", body, re.MULTILINE))
else:
    body = ""
    entry_count = 0

if entry_count > 0:
    def renumber(m, start=[next_entry_num]):
        new_n = start[0]
        start[0] += 1
        return f"### {new_n}."
    renumbered = re.sub(r"^### \d+\.", renumber, body, flags=re.MULTILINE)
    with open("docs/llms-full.txt", "a", encoding="utf-8") as f:
        f.write("\n" + renumbered.rstrip() + "\n")
```

If `entry_count == 0` (out-of-scope abort, or all-access-methods-failed), skip the merge — `llms-full.txt` is unchanged. The PR still opens with the doc updates from Step 6 so the source is registered.

---

## Step 8 — Rebuild derived files

```bash
cd docs && python build_tags.py
```

Regenerates `data.json`, `llms.txt`, `tags/*.md`, `gem-knowledge.txt`. If it exits non-zero: **critical failure** — record it and continue to Step 9. The PR still opens.

---

## Step 9 — Commit, push, open PR

```bash
DATE=$(date -u +%Y-%m-%d)
SLUG=$(echo "[SOURCE_NAME]" | tr '[:upper:]' '[:lower:]' | tr -s ' ' '-' | tr -d -c 'a-z0-9-')

rm -f docs/staging/new-source-$SLUG-$DATE.txt

git checkout -b "claude/new-source-$SLUG-$DATE" 2>/dev/null || git checkout -b "claude/new-source-$SLUG-$DATE-2"
git add docs/llms-full.txt docs/llms.txt docs/data.json docs/gem-knowledge.txt docs/tags/ \
        meta/source-targets.json meta/sources-inventory.md meta/source-audit.md \
        meta/sources-log.md meta/automation-prompt.md
git commit -m "Add new source: [SOURCE_NAME] (N entries)"
git push -u origin HEAD
```

**Open the PR** via the agent's built-in GitHub tools (preferred) or `gh pr create` as fallback:

```bash
gh pr create \
  --base main \
  --head "$(git rev-parse --abbrev-ref HEAD)" \
  --title "Add new source: [SOURCE_NAME]" \
  --body "$(cat <<'EOF'
## New source onboarding: [SOURCE_NAME]

Closes #[LINKED_ISSUE]

**Homepage:** [HOMEPAGE_URL]
**Access method:** [sitemap | listing | api | playwright | manual]
**URL pattern:** `[pattern]`
**Estimated known total:** [number or range]
**Priority assigned:** [PRIORITY]

## Initial pass

- Entries staged: N (of [INITIAL_PASS_SIZE] attempted)
- Dropped (out of scope): N
- Non-critical failures: N
- Critical failure: NONE | <description>

## Files updated

- `docs/llms-full.txt`: appended N entries (numbers M–M+N-1)
- `meta/source-targets.json`: added "[SOURCE_NAME]" with priority [PRIORITY], known_total [N]
- `meta/sources-inventory.md`: catalog entry added
- `meta/source-audit.md`: access matrix row added
- `meta/sources-log.md`: attempt logged
- `meta/automation-prompt.md`: source added to the weekly routine's source list

## Reviewer checklist

- [ ] Source meets `meta/inclusion-criteria.md` Level 1 (editorial accountability, public access, relevance)
- [ ] Access method documented matches reality (spot-check by re-running listing fetch)
- [ ] Spot-check 2–3 entries for description quality and tag accuracy
- [ ] Source name in `source-targets.json` matches `source:` field used in staged entries
- [ ] Priority and known_total feel reasonable

## After merge — required manual step

The cloud routine on claude.ai/code/routines has the automation prompt snapshotted at creation time. To make the weekly routine actually check this new source, update the routine's Instructions field on the web UI to match the new `meta/automation-prompt.md` (paste the content between PROMPT START and PROMPT END).

EOF
)"
```

If `gh` is missing, the cloud session's built-in GitHub tools should still work; if both fail, log it as a critical failure — the branch is pushed, so the maintainer can open the PR manually.

---

## Failure handling — recap

**Non-critical** (continue; record in PR body):
- Some publication pages 403 / 404 → skip those entries.
- Sitemap missing some sub-sitemaps → note in PR; backlog will catch later.
- One Playwright attempt fails → log and move on.

**Critical** (still open the PR; flag prominently):
- All access methods fail → no entries staged; source still registered in canonical files as "manual / no auto-access."
- `build_tags.py` exits non-zero.
- `git push` fails.
- PR creation fails after fallback.

Better to land a noisy PR with clear failure messaging than to silently abort.

---

## Step 10 — Print final summary

Print to the session transcript:
- Source name and access method discovered
- Entries staged / dropped / failed
- PR URL (or branch name if PR creation failed)
- Reminder: routine on claude.ai/code/routines needs the updated automation prompt pasted in for the weekly check to include this source.

## PROMPT END

---

## After each onboarding (manual)

The PR is the review surface. To merge:

1. Open the PR on GitHub. Read the access-method discovery — does the pattern look right?
2. Spot-check 2–3 of the staged entries.
3. Review the `source-targets.json` row and the `source-audit.md` matrix addition.
4. If everything looks good, merge.
5. **Update the routine on claude.ai/code/routines** — paste the updated `meta/automation-prompt.md` into the Instructions field so next week's run includes the new source.

If you reject the source after seeing the PR, close it. The branch can be deleted; the canonical docs were only modified on the branch, so closing reverts everything.
