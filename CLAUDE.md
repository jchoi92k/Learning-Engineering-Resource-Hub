# Renaissance AI and Education Resource Hub

**Start here:** `index.md` (public navigation map). **Operational guide for agents:** `meta/agent-guide.md` — read this before doing any indexing work. Contains entry format, tag schema, source URL patterns, current state, and subagent protocol.

---

## Critical rules

**Hosting.** GitHub Pages (public). Local dev server: `python -m http.server 8765` from `docs/`. Do not suggest Netlify, Vercel, or other cloud hosting.

**No inference.** Entry descriptions must come from fetched page content. If a page returns 403/404 or can't be loaded, drop the entry. Never write descriptions from titles alone.

**Subagents write to files.** Any agent collecting entries must write output to `docs/staging/{source}.txt`, not return data as text in the response. Data returned as text is lost on context compaction.

**UTF-8 only.** All files must be UTF-8 (no BOM). Always use `encoding="utf-8"` when writing files. `build_tags.py` validates encoding at build time and rejects mojibake.

**Private folder.** `private/` is gitignored and holds meeting notes, internal strategy, research drafts, and the canonical decisions log. Never echo its contents into commits, PR bodies, public docs, or external channels. If something there feels useful publicly, propose moving it to `meta/` — don't copy or paraphrase.

---

## Logging rules (process)

**Decisions log.** All major decisions — indexing judgment calls, architectural choices, roadmap changes, repo structure changes — are appended to `private/decisions.md` with a dated session heading and `**Decision:** / **Why:**` blocks. Newest session at top. Do not edit historical entries; if reversing a decision, append a new one.

**Do not log decisions by editing other docs.** If a decision affects an existing document, update the document with the new state, but record the decision itself only in `private/decisions.md`.

**Index new markdown files.** Any new `.md` added to `meta/` is registered in `index.md` (root) with a one-line description. Any new `.md` added to `private/` is registered in `private/index.md`. Build/referatory artifacts (auto-generated files, scripts, JSON data) do not need indexing. If you can't summarize a new file in one line, you may not need the file.

**Categorization default for new files.** Default to `private/` unless the file adds clear value to a public audience (new contributors, cold-starting agents, end users). Operational guides, source catalogs, prompts, and content standards belong in `meta/`. Strategy, positioning, research drafts, and meeting notes belong in `private/`.

**Keep `meta/agent-guide.md` and `CLAUDE.md` Current state fresh.** When entry count crosses a hundred-mark (e.g. 1,200, 1,300), when a new source is added, or when a source's access method materially changes (now needs Playwright, newly blocked, etc.), update both files' Current state sections in the same commit. The per-source live counts live in `docs/data.json` (`meta.coverage`), but the agent-facing summary in CLAUDE.md and agent-guide.md needs to be kept in sync manually. Drift in these files has previously left cold-start agents reading stale context (agent-guide drifted from 569 to 1,181 before being refreshed 2026-05-13).

---

## Scope

All evidence-based K-12 and higher education — not limited to learning engineering methods. Primary sources: WWC, LPI, EdTrust, NAP, CASEL, JEDM, Evidence for ESSA, and others catalogued in `meta/sources-inventory.md`.

OpenAlex / Semantic Scholar / CrossRef / Unpaywall are **utility APIs only** — used to retrieve abstracts for paywalled entries or find OA versions. They are not primary indexing targets.

---

## Current state (as of 2026-05-13)

- **1,181 entries** in `docs/llms-full.txt`
- Sources: WWC (29 guides + ~178 intervention reports), LPI (36), EdTrust (31), JEDM (39), Evidence for ESSA (78), JLA (43), Campbell Collaboration (45), Brookings (23), IES REL (30), Digital Promise (254), TNTP (36), UChicago Consortium (31), Datasets (101 total), AIMS Collaboratory (53), Tools Competition (18), LEVI Math (7), Benchmarks & Code (11), NAP (2), CASEL (1), UNESCO (3), CAST (1), CMU/ETS (1), WestEd (14), NWEA (70), Mathematica (32)
- JS-paginated sources: use `python meta/playwright-scrape.py [tntp|digital-promise]`
- Coverage tracking: `meta/source-targets.json` + `data.json` meta.coverage
- After any edits, run `python build_tags.py` from `docs/` to regenerate `data.json` and tag files
