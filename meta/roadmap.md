# Roadmap

> Open items and planned work, in rough priority order. Current operational state lives in `agent-guide.md`; this file is the to-do list. Move an item out when it lands or is dropped.

## Corpus quality

- **Revise the keyword auto-tags.** Tags on rows inserted by the pipeline since 2026-06-04 come from a keyword-regex pass in `scripts/process_staged.py` and are noisy (for example `formative-assessment` on a teacher-licensure brief, `dropout-prevention` on an accountability report). The plan is one bulk revision pass rather than piecemeal edits; until then the weekly review adds tags where the description makes them obvious and leaves pipeline tags in place. The same pass should cover the roughly 850 published rows that carry no tags at all.
- **`evidence_rating` field** for WWC and Evidence for ESSA entries (WWC tiers, ESSA Strong / Moderate / Promising), so reports that were reviewed but found no qualifying evidence could be shown with their rating instead of being held out. Schema, build and MCP worker change.
- **CASEL backfill** — parked on a site outage; the source has a 60 s crawl delay and needs a detail fetch per item, so it runs manually, not in the weekly list.

## Agent-facing delivery

- **Metadata backfill, remainder.** The 2026-09-15/16 backfill dated 3,305 published entries (392 n/a, 207 undated) and put authors on 2,679. Left: the 70 NWEA, 31 EdTrust, 2 LPI and 4 Mathematica May rows with no stored record (no longer on their listings; only a targeted page pass would date them), 70 WestEd pages with no copyright line, 8 REL partnership pages, 11 AIMS pages without metadata. EdTrust authors are deliberately empty (the co-author taxonomy exposes login handles, not names); WWC and TNTP pages carry no byline.
- **`document_url` exposure and coverage.** The direct report link is stored on 493 rows (WestEd, JEDM, JLA, TNTP, AIMS) but not yet in `data.json`, `llms-full.txt` or the MCP worker. Coverage passes still to run: Mathematica (`mprpublicationurl` is in the API record; ~150 API pages, now kept in the raw sidecar), the ~400 WestEd pages fetched before the selector existed, UChicago / LPI / NWEA item pages. WWC PDFs sit behind JavaScript and Digital Promise bitstreams need a per-item call.
- **Publisher type label.** Expose the source's own type string ("Brief", "Practice Guide", "Research and Evaluation"), already in most raw items, alongside the coarse `type` enum.
- **Per-source access policy.** A per-source table of each source's agent-access posture — robots.txt stance, `llms.txt` present y/n, and whether an agent can fetch the resource/PDF directly (some 403, some allow) — grounded in the robots URLs already in the configs and our own fetch logs. Fold the fields into the existing `list_sources` MCP tool output and mirror them in a static table (e.g. `meta/source-access.md`); no separate endpoint needed. Needs periodic re-checking since policies drift, and publish only what we've verified.

## Weekly update

- **Skill refinements surfaced by the 2026-09-14 run:** restate the research-outputs genre rule inside the row-review step of `/weekly-update` (a webinar series and an "impact story" slipped through as `report`); add a rule for removing unsupported pipeline tags, or say explicitly that removal waits for the bulk revision; extend the description-upgrade rule from `page-meta` teasers to one-sentence `listing` blurbs when page text is stored on the row.
- **Move the run to a cloud cron** (GitHub Actions running `scripts/update.sh`, then `claude-code-action` invoking `/weekly-update`, then a publish job that opens the PR). Preconditions: local runs judged stable, a read-only dispatch workflow proving the runner's IP can reach every source, and a model choice for the cron.
- **Retire `sources/*-backlog.txt`** — `scrape.py` still writes these on every run; pending rows in hub.db carry that role now.

## Test suites

- **Testing rule for agent-added tests** in `AGENTS.md` and the `/weekly-update` skill: one behavior per test, named after it; assert results, not call order; small tests by default; every new test states the incident, contract or rule it guards; no tests for trivial code or unreachable cases; tests written in the same pass as the code get a fresh-context review before commit. Cheap and the piece that stops the pattern recurring.
- **Split the MCP worker suite by size.** All 42 cases in `worker/test-mcp.mjs` run over HTTP against a spawned dev worker and the pure logic in `worker/src/index.js` has no unit tests because nothing is exported. Export the filters, sorts, `formatEntry` and `findRelated`, test them with `node:test` against `docs/data.json`, and shrink the transport suite to about 12–15 cases so it stays under the worker's own 100-requests-per-minute limit (it exceeded it on 2026-09-15). Do this the next time the worker is touched.
- **Consolidate the Python suite** (103 cases): parametrize the one-line `json_path` and `early_stop` cases, merge the overlapping `clean_text` / `strip_html` cases, split or name the multi-scenario tests, replace the wall-clock throttle test with an injected clock, assert named columns instead of whole rows where the row is not the contract. Tidiness only; about 85–90 cases when done.

## Open questions

- Whether WestEd `Collection` items belong in `sources/wested.json`'s `type_allow` list. The 19 published ones mix evaluation-report collections with resource landing pages (2026-09-14 review).
