# Learning Engineering Resource Hub

**Full operational guide**: `meta/agent-guide.md` — read this before doing any indexing work. Contains entry format, tag schema, source URL patterns, current state, and subagent protocol.

---

## Critical rules

**Hosting.** GitHub Pages (public). Local dev server: `python -m http.server 8765` from `docs/`. Do not suggest Netlify, Vercel, or other cloud hosting.

**No inference.** Entry descriptions must come from fetched page content. If a page returns 403/404 or can't be loaded, drop the entry. Never write descriptions from titles alone.

**Subagents write to files.** Any agent collecting entries must write output to `docs/staging/{source}.txt`, not return data as text in the response. Data returned as text is lost on context compaction.

---

## Scope

All evidence-based K-12 and higher education — not limited to learning engineering methods. Primary sources: WWC, LPI, EdTrust, NAP, CASEL, JEDM, Evidence for ESSA, and others catalogued in `meta/sources-inventory.md`.

OpenAlex / Semantic Scholar / CrossRef / Unpaywall are **utility APIs only** — used to retrieve abstracts for paywalled entries or find OA versions. They are not primary indexing targets.

---

## Current state (as of 2026-05-04)

- **487 entries** in `docs/llms-full.txt`
- Sources: WWC (29 guides + ~98 intervention reports), LPI (30), EdTrust (30), JEDM (30), Evidence for ESSA (29), JLA (25), Campbell Collaboration (25), Brookings (22), IES REL (30), Digital Promise (30), Datasets (101 total: 33 NCES, 11 IEA, 12 CMU DataShop, 9 Harvard/OI, 8 OECD, 4 Stanford CEPA, 4 US Dept of Ed, 3 WPI/ASSISTments, 3 World Bank, 3 NSC, 2 Urban, 2 ICPSR, 2 Duolingo, 2 NBER, 1 CRDC, 1 Open Univ, 1 Riiid), NAP (2), CASEL (1), UNESCO (3), CAST (1), CMU/ETS (1)
- After any edits, run `python build_tags.py` from `docs/` to regenerate `data.json` and tag files
