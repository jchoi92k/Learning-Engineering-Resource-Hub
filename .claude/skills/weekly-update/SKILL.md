---
name: weekly-update
description: Weekly corpus refresh for the Renaissance hub. Runs scripts/update.sh, repairs a failed source by editing its sources/*.json only, reviews the new rows with curate.py (scope, tags, description upgrades from stored page text), verifies the build, and writes docs/staging/pr-body.md. Never commits, pushes or opens a pull request.
argument-hint: '[--sources "lpi wwc ..."] [--dry-run]'
allowed-tools: Read, Grep, Glob, Edit(sources/**), Write(docs/staging/**), Bash(bash scripts/update.sh*), Bash(python scripts/*), Bash(python -m pytest*), Bash(ruff check*), Bash(git status*), Bash(git diff*), Bash(git log*), Bash(ls*), Bash(cat docs/staging/*), Bash(head*), Bash(tail*)
---

# /weekly-update

You are the review step of the weekly update. The mechanics are all in scripts; your job is judgment: notice what the pipeline could not, fix only what a config change can fix, and leave a maintainer a PR body they can trust at a glance. Arguments to this skill go straight to `scripts/update.sh` (`$ARGUMENTS`); with none, it runs the full weekly source list.

## Rules that override everything else

- **Only scripts write `hub.db`**: `process_staged.py`, `verify_urls.py`, `curate.py`. Never run SQL against it and never edit files under `docs/` by hand — they are regenerated.
- **Your edit surface is `sources/*.json`** (plus files under `docs/staging/`, which are not committed). Do not modify `scripts/`, `.github/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, `sources/*.md` or `meta/`. If one of those needs a change, describe it in the PR body.
- **Never commit, push, merge, or open a PR.** Stop after writing `docs/staging/pr-body.md`.
- **No ad-hoc HTTP.** Every request goes through `scripts/scrape.py` (throttled, logged, audited). To look at a live listing, use `python scripts/scrape.py <src> --test`. Do not use WebFetch or curl against the sources, and never fetch an item page to write a description — use the page text already stored on the row (step 3).
- **One config attempt per source.** If a source still fails after one edit and re-test, revert the edit (`git diff sources/` shows it) and report.
- **One pipeline run at a time.** If `docs/staging/update.lock` exists when you start, a run is active or died: do not start another; report.
- **A throttle warning stops you.** Each scrape log ends with a request audit; a repeated URL or a gap below the delay means: no more requests this run, report it.
- **Descriptions come from the source.** Never write one from a title. The only description you may write is the `llm-summary` upgrade in step 3, grounded in the row's stored `page_text`.

## Procedure

### 0. Preconditions

1. `git status --short`: the tree should be clean apart from files under `docs/staging/`. Anything else is a maintainer's work in progress — report it and stop.
2. `ls docs/staging/update.lock` must fail (no lock).
3. Note the time; the pipeline rewrites `docs/staging/run-summary.md` when it finishes.

### 1. Run the pipeline

```bash
bash scripts/update.sh $ARGUMENTS
```

A full run makes a few hundred throttled requests and can exceed the Bash tool's foreground timeout: run it in the background and wait for the `[update] Summary written to docs/staging/run-summary.md` line in its output (or a fresh mtime on the file). Do not start a second run while waiting. Its exit code is non-zero only when a pipeline step (process / verify / build) failed — a failing *source* never aborts the run.

### 2. Triage the sources

Read `docs/staging/run-summary.md`. For every row whose Status is not `ok`, read `docs/staging/logs/<src>.log` (scrape and process output) and `docs/staging/logs/<src>-requests.log` (one line per request, then the audit).

| Status | What to do |
|---|---|
| `ok` | Nothing. |
| `partial (fetch failures)` | Read the request log. HTTP 403 / 429 or connection errors from the source: report, do not retry (the throttle clock and robots delay are already applied). A transient error on one page: nothing — next week's run picks it up. |
| `empty (0 items extracted …)` | Selector drift or a block. Run `python scripts/scrape.py <src> --test`. If the page loads but yields no items, compare the selectors in `sources/<src>.json` with the test output and the `## Entry metadata` section of `sources/<src>.md`; make **one** config edit; run `--test` again. If it passes: `python scripts/scrape.py <src>` then `python scripts/process_staged.py <src>` and add the source's inserts to your review in step 3. If it still fails, revert and report. If the request log shows 403 / 429: report, no retry. |
| `scrape failed (exit N)` | Read the traceback in the log. A config problem (invalid JSON, missing key, bad URL) gets the same one-attempt treatment. A code error is not yours to fix: report it with the traceback. |
| `process_staged failed` | Pipeline failure. Read the log, report it, do not re-run: the staging file stays on disk and a maintainer re-runs after fixing the cause. |

If the summary says URL verification or the build FAILED, read `docs/staging/logs/verify.log` or `docs/staging/logs/build.log` and report; do not work around it.

### 3. Review the new rows

The summary's `**Rows added:** num A–B` line gives the range (absent when nothing was inserted → skip to step 5). List them:

```bash
python scripts/curate.py recent --since-num <A-1> --json
```

Rows with `excluded = 1` and reason `no_description_pending` are backlog items (the listing had no blurb); count them and move on. For each active row, in this order:

1. **Scope** — the test is `docs/purpose.md` § Scope: learning or teaching must be the central activity. Exclude only a clear miss (`python scripts/curate.py exclude <num> --reason out_of_scope`); the published examples are military/veteran welfare, adult disability employment, agricultural extension. When unsure, keep the row and list it under "Needs a human" in the PR body.
2. **Description** — read it. It must be the publisher's text (`description_source` = `listing`, `page-meta` or `page-abstract`). If it is boilerplate ("Read more", cookie text, the title repeated) or cut mid-sentence, that is a *config* problem: do not rewrite it; note the row and the likely selector in the PR body.
3. **Tags** — the vocabulary is the list in `docs/schema.md`; `set-tags` refuses anything else. Add a tag only when the description makes it obvious (a randomized trial without `rct`, a mathematics study without `math-education`, a K-12 study without `k-12`). `python scripts/curate.py set-tags <num> "tag1,tag2,…"` replaces the whole set, so pass the existing tags plus the additions. In doubt, leave the tags alone.
4. **`page-meta` teasers** (today: EdTrust) — a one-sentence meta description is thin. Run `python scripts/curate.py show <num> --json` and look at `raw_item.page_text`. If it holds at least a few paragraphs of the article, write two or three sentences that say what the piece examines, for whom, and its main finding or argument as stated in that text — nothing that is not in `page_text`. Save it to `docs/staging/desc-<num>.txt` and apply `python scripts/curate.py set-description <num> --source llm-summary --file docs/staging/desc-<num>.txt`. No `page_text`, or only a stub: leave the teaser as it is.

Every `curate.py` write prints the before/after; keep those for the PR body.

### 4. Verify

After any `curate.py` write, regenerate and check:

```bash
python scripts/build_from_db.py
python scripts/build_from_db.py --check
python -m pytest tests/ -q
ruff check scripts/ tests/
```

All four must pass. If `--check` fails on something you did not touch, report rather than fix.

### 5. Write the PR body and stop

Write `docs/staging/pr-body.md`:

```markdown
## Weekly update — YYYY-MM-DD

**New entries:** N (nums A–B) · **Pending (no description on the source):** N · **Excluded this review:** N

<the Source | Status table from run-summary.md>

### Config changes
- `sources/<src>.json`: what changed and why (or "none")

### Review
- Out of scope (excluded): #num — title — one-line reason (or "none")
- Tags added: #num +tag (or "none")
- Descriptions upgraded (page-meta → llm-summary): #num (or "none")

### Needs a human
- Sources still failing after one attempt, with the error
- Rows you were unsure about (scope, boilerplate descriptions, suspected selector drift)
- Throttle audit warnings, if any
- Anything that would need a change outside sources/*.json

### Commands run
- one line per command that changed state
```

Print the path of the PR body and the "Needs a human" section, then stop. A maintainer commits, pushes, deploys.

## Quiet week

If the summary shows 0 new entries, 0 pending and every source `ok`, write a two-line `pr-body.md` saying so and stop. Nothing is opened for a quiet week (decision of 2026-08-30).

## Reference

- `AGENTS.md` — the rules above, in full
- `sources/README.md` — config keys, run modes, backlog convention, the request audit
- `docs/schema.md` — fields, `description_source` provenance, tag vocabulary
- `docs/purpose.md` — scope
- `sources/<src>.md` — what each source's pages look like (selectors, quirks)
