# Learning Engineering Resource Hub — Purpose

## What This Is

A **referratory** (not a repository) of 569+ evidence-based K-12 and higher education resources.
It links to externally-hosted content; it does not host, mirror, or reproduce source material.
Original scope was AIMS Collaboratory only (74 entries, 2026-04-27); expanded to broad
evidence-based education sources across multiple collection rounds.

## How It Fits the LLM-Facing Wiki Landscape

This hub follows the **llms.txt standard** (Jeremy Howard / Answer.AI, Sept 2024):
- `/llms.txt` — LLM entry point: navigation guide + compact index of all entries (~31K tokens)
- `/llms-full.txt` — full content dump with descriptions (~125K tokens, too large for most web fetchers)
- `tags/*.md` — per-tag detail files (500–5,000 tokens each), linked from llms.txt

This is a **static referratory**, not a Karpathy-style LLM-maintained wiki (where the LLM writes
the pages). The content here is human-curated; the format is optimized for LLM consumption.
See `docs/llm-wiki-landscape.md` for a full landscape analysis.

## Primary Audience

LLM agents with WebFetch capability. The index is formatted for direct consumption by
a language model, not for human browsing. Structure choices (flat files, dense markdown,
stable URLs) are made to minimize fetches and maximize in-context reasoning.

## Scope

**In scope:**
- All evidence-based K-12 and higher education resources from pre-curated organizations
- Sources: WWC, LPI, EdTrust, JEDM, JLA, Evidence for ESSA, Campbell Collaboration, Brookings, IES REL, Digital Promise, AIMS Collaboratory, Tools Competition, LEVI Math, NAP, CASEL, UNESCO, CAST, and more
- All resource types (papers, code, tools, frameworks, reports, datasets, benchmarks)
- Education datasets from NCES, IEA, CMU DataShop, OECD, ASSISTments, Duolingo, Stanford CEPA, etc.

**Out of scope:**
- Individual student-level data (FERPA-protected; this hub indexes metadata only)
- Resources that cannot be verified via direct page fetch

## What a Querying Agent Should Expect

1. Fetch `llms.txt` for the compact index with navigation guide (recommended entry point)
2. Use tag file URLs in llms.txt to drill into specific topics
3. Every entry has: title, type, URL, source, tags
4. Full descriptions are in `llms-full.txt` (large) or per-tag files (small)
5. `url_confirmed: false` signals URLs not directly verified during compilation

## Maintenance Model

Entries are collected from source organization websites, validated via direct page fetch,
and appended to `llms-full.txt`. Running `python build_tags.py` regenerates `llms.txt`,
`data.json`, and `tags/*.md`. See `meta/agent-guide.md` for the full operational guide.
