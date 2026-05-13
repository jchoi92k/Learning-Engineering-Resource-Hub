# Renaissance AI and Education Resource Hub — Purpose

## What this is

A **referatory** (not a repository) of 1,181+ evidence-based K-12, higher-education, and learning-engineering research resources. It links to externally-hosted content; it does not host, mirror, or reproduce source material. Original scope was AIMS Collaboratory only (74 entries, 2026-04-27); expanded across multiple collection rounds into a multi-source curated index.

## How it fits the LLM-facing landscape

This hub follows the **llms.txt standard** (Jeremy Howard / Answer.AI):

- `llms-full.txt` — primary file: all entries with descriptions + auto-generated navigation header.
- `llms.txt` — compact index (titles, URLs, types, tags — no descriptions).
- `tags/*.md` — per-tag detail files (generated, consumed by the web UI).
- An MCP server (Cloudflare Worker) exposes the corpus to agents that prefer programmatic queries.

This is a **static referatory**, not a Karpathy-style LLM-maintained wiki (where the LLM writes the pages). Content here is human-curated; the format is optimized for LLM consumption.

## Primary audience

Two audiences, in this order:

1. **LLM agents** with WebFetch / MCP capability — the index is formatted for direct consumption by a language model, not for human browsing. Structure choices (flat files, dense markdown, stable URLs) minimize fetches and maximize in-context reasoning.
2. **Human researchers and practitioners** — the `index.html` UI provides browse-by-tag, browse-by-source, and full-text search over the same corpus.

## Scope

**In scope:**

- All evidence-based K-12 and higher education resources from pre-curated organizations
- Sources include: What Works Clearinghouse, Learning Policy Institute, Education Trust, JEDM, JLA, Evidence for ESSA, Campbell Collaboration, Brookings (Brown Center), IES Regional Education Labs, Digital Promise, TNTP, NWEA, Mathematica, WestEd, UChicago Consortium, CREDO at Stanford, AIMS Collaboratory, Tools Competition, LEVI Math, NAP, CASEL, UNESCO, CAST, and more
- All resource types: papers, code, tools, frameworks, reports, datasets, benchmarks
- Education datasets from NCES, IEA, CMU DataShop, OECD, ASSISTments, Duolingo, Stanford CEPA, etc.

**Out of scope:**

- Individual student-level data (FERPA-protected; this hub indexes metadata only)
- Resources that cannot be verified via direct page fetch (no-inference policy — descriptions must come from fetched content, never from titles alone)
- Topics where learning or teaching is not the central activity (military/veteran welfare, adult disability employment, agricultural extension, etc.)

## What a querying agent should expect

1. Fetch `llms-full.txt` for all entries with descriptions (recommended).
2. The file header contains a tag directory, source list, and usage instructions.
3. Every entry has: title, type, URL, source, tags, and a 1–3 sentence description.
4. `url_confirmed: false` signals URLs not directly verified during compilation (rare — usually flagged as a known broken entry in `meta/agent-guide.md`).

## Maintenance model

Entries are collected from source organization websites, validated via direct page fetch, and appended to `llms-full.txt`. Running `python build_tags.py` regenerates `llms.txt`, `data.json`, `tags/*.md`, and `gem-knowledge.txt`.

The weekly automated check runs as a cloud routine (Anthropic-managed Claude Code session) using the prompt at `meta/automation-prompt.md`. It opens a PR with new entries each week. Backlog runs for specific sources use `meta/backlog-prompt.md`.

For the full operational guide, see `meta/agent-guide.md`.
