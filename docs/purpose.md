# Renaissance AI and Education Resource Hub — Purpose

## What this is

A **referatory** (not a repository) of evidence-based K-12, higher-education, and learning-engineering research resources. It links to externally-hosted content; it does not host, mirror, or reproduce source material.

## How it fits the LLM-facing landscape

This hub follows the **llms.txt standard** (Jeremy Howard / Answer.AI):

- `llms-full.txt` — primary file: all entries with descriptions + auto-generated navigation header.
- `llms.txt` — compact index (titles, URLs, types, tags — no descriptions).
- `tags/*.md` — per-tag detail files (generated, consumed by the web UI).
- An MCP server (Cloudflare Worker) exposes the corpus to agents that prefer programmatic queries.
- A Gemini Gem provides conversational access for users who prefer chat.

This is a **static referatory**, not an LLM-maintained wiki. Content is human-curated; the format is optimized for LLM consumption.

## Primary audience

Two audiences, in this order:

1. **LLM agents** with WebFetch / MCP capability — the index is formatted for direct consumption by a language model. Structure choices (flat files, dense markdown, stable URLs) minimize fetches and maximize in-context reasoning.
2. **Human researchers and practitioners** — the `index.html` UI provides browse-by-tag, browse-by-source, and full-text search over the same corpus.

## Scope

**In scope:**

- All evidence-based K-12 and higher education resources from pre-curated organizations
- Sources include: What Works Clearinghouse, Mathematica, Learning Policy Institute, Digital Promise, Evidence for ESSA, NWEA Research, AIMS Collaboratory, Campbell Collaboration, TNTP, Education Trust, UChicago Consortium, IES Regional Education Labs, NCES, Brookings, CREDO at Stanford, WestEd, CASEL, National Academies Press, and more
- All resource types: papers, code, tools, frameworks, reports, datasets, benchmarks
- Education datasets from NCES, IEA, CMU DataShop, OECD, ASSISTments, Duolingo, Stanford CEPA, etc.

**Out of scope:**

- Individual student-level data (FERPA-protected; this hub indexes metadata only)
- Resources that cannot be verified via direct page fetch (no-inference policy — descriptions must come from fetched content, never from titles alone)
- Topics where learning or teaching is not the central activity (military/veteran welfare, adult disability employment, agricultural extension, etc.)

## What a querying agent should expect

1. Fetch `llms-full.txt` for all entries with descriptions (recommended).
2. The file header contains a tag directory, source list, and usage instructions.
3. Every entry has: title, type, URL, source, tags, and a 1-3 sentence description.
4. `url_confirmed: false` signals URLs not directly verified during compilation.

## Maintenance model

Entries are collected from source organization websites, validated via direct page fetch, and inserted into `data/hub.db` (SQLite). Running `python scripts/build_from_db.py` regenerates all published files: `llms-full.txt`, `llms.txt`, `data.json`, `tags/*.md`, and `gem-knowledge.txt`.

The weekly automated check uses the prompt at `meta/automation-prompt.md`. It checks all sources for new content and stages new entries. Backlog runs for specific sources use `meta/backlog-prompt.md`.

Want a source included? Open a [New source suggestion](https://github.com/jchoi92k/Learning-Engineering-Resource-Hub/issues/new?template=new-source.md) issue.

For the full operational guide, see `meta/agent-guide.md`.
