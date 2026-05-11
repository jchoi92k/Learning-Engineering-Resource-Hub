# Renaissance AI and Education Resource Hub

**Full operational guide**: `meta/agent-guide.md` — read this before doing any indexing work. Contains entry format, tag schema, source URL patterns, current state, and subagent protocol.

---

## Critical rules

**Hosting.** GitHub Pages (public). Local dev server: `python -m http.server 8765` from `docs/`. Do not suggest Netlify, Vercel, or other cloud hosting.

**No inference.** Entry descriptions must come from fetched page content. If a page returns 403/404 or can't be loaded, drop the entry. Never write descriptions from titles alone.

**Subagents write to files.** Any agent collecting entries must write output to `docs/staging/{source}.txt`, not return data as text in the response. Data returned as text is lost on context compaction.

**UTF-8 only.** All files must be UTF-8 (no BOM). Always use `encoding="utf-8"` when writing files. `build_tags.py` validates encoding at build time and rejects mojibake.

---

## Scope

All evidence-based K-12 and higher education — not limited to learning engineering methods. Primary sources: WWC, LPI, EdTrust, NAP, CASEL, JEDM, Evidence for ESSA, and others catalogued in `meta/sources-inventory.md`.

OpenAlex / Semantic Scholar / CrossRef / Unpaywall are **utility APIs only** — used to retrieve abstracts for paywalled entries or find OA versions. They are not primary indexing targets.

---

## Current state (as of 2026-05-10)

- **981 entries** in `docs/llms-full.txt`
- Sources: WWC (29 guides + ~147 intervention reports), LPI (30), EdTrust (30), JEDM (30), Evidence for ESSA (65), JLA (25), Campbell Collaboration (45), Brookings (22), IES REL (30), Digital Promise (254), TNTP (36), UChicago Consortium (30), Datasets (101 total), AIMS Collaboratory (53), Tools Competition (18), LEVI Math (7), Benchmarks & Code (11), NAP (2), CASEL (1), UNESCO (3), CAST (1), CMU/ETS (1)
- JS-paginated sources: use `python meta/playwright-scrape.py [tntp|digital-promise]`
- Coverage tracking: `meta/source-targets.json` + `data.json` meta.coverage
- After any edits, run `python build_tags.py` from `docs/` to regenerate `data.json` and tag files
