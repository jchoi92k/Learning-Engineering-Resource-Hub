# Roadmap

> Open items and planned work, in rough priority order. Current operational state lives in `agent-guide.md`; this file is the to-do list. Move an item out when it lands or is dropped.

## Corpus quality

- **Revise the keyword auto-tags.** Tags on rows inserted by the pipeline since 2026-06-04 come from a keyword-regex pass in `scripts/process_staged.py` and are noisy (for example `formative-assessment` on a teacher-licensure brief, `dropout-prevention` on an accountability report). The plan is one bulk revision pass rather than piecemeal edits; until then the weekly review adds tags where the description makes them obvious and leaves pipeline tags in place. The same pass should cover the roughly 850 published rows that carry no tags at all.
- **`evidence_rating` field** for WWC and Evidence for ESSA entries (WWC tiers, ESSA Strong / Moderate / Promising), so reports that were reviewed but found no qualifying evidence could be shown with their rating instead of being held out. Schema, build and MCP worker change.
- **CASEL backfill** — parked on a site outage; the source has a 60 s crawl delay and needs a detail fetch per item, so it runs manually, not in the weekly list.

## Weekly update

- **Skill refinements surfaced by the 2026-09-14 run:** restate the research-outputs genre rule inside the row-review step of `/weekly-update` (a webinar series and an "impact story" slipped through as `report`); add a rule for removing unsupported pipeline tags, or say explicitly that removal waits for the bulk revision; extend the description-upgrade rule from `page-meta` teasers to one-sentence `listing` blurbs when page text is stored on the row.
- **Move the run to a cloud cron** (GitHub Actions running `scripts/update.sh`, then `claude-code-action` invoking `/weekly-update`, then a publish job that opens the PR). Preconditions: local runs judged stable, a read-only dispatch workflow proving the runner's IP can reach every source, and a model choice for the cron.
- **Retire `sources/*-backlog.txt`** — `scrape.py` still writes these on every run; pending rows in hub.db carry that role now.

## Open questions

- Whether WestEd `Collection` items belong in `sources/wested.json`'s `type_allow` list. The 19 published ones mix evaluation-report collections with resource landing pages (2026-09-14 review).
