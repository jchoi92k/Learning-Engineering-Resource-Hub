# Learning Engineering Resource Hub — Purpose

## What This Is

A **referratory** (not a repository) of 84 learning engineering and AI-in-education resources.
It links to externally-hosted content; it does not host, mirror, or reproduce source material.
Original scope was AIMS Collaboratory only (74 entries, 2026-04-27); expanded to broader
learning engineering sources in 2026-05-01 revision.

## How It Fits the LLM-Facing Wiki Landscape

This hub follows the **llms.txt standard** (Jeremy Howard / Answer.AI, Sept 2024):
- `/llms.txt` — discovery layer (curated index of key sections and files)
- `/llms-full.txt` — full content dump (all 84 entries in one fetch)
- Per-category files in `by-domain/` and `tags/` for scoped queries

This is a **static referratory**, not a Karpathy-style LLM-maintained wiki (where the LLM writes
the pages). The content here is human-curated; the format is optimized for LLM consumption.
See `docs/llm-wiki-landscape.md` for a full landscape analysis.

## Primary Audience

LLM agents with WebFetch capability. The index is formatted for direct consumption by
a language model, not for human browsing. Structure choices (flat files, dense markdown,
stable local URLs) are made to minimize fetches and maximize in-context reasoning.

## Scope

Resources listed on the AIMS Collaboratory "Inventory of Public Goods" page as of
2026-04-27. Scope includes: papers, reports, code repositories, frameworks, platforms,
blog posts, presentations, and project websites from AIMS partner organizations.

**In scope:**
- Resources from AIMS Collaboratory (scraped 2026-04-27)
- Learning engineering field resources: TLA, CMU LearnLab, Simon Initiative, ASSISTments, PSLC DataShop
- K-12 AI policy resources: CoSN guidance, district readiness tools
- All resource types (papers, code, tools, frameworks, reports, blog posts, presentations, datasets)

**Out of scope:**
- CMU DataShop datasets (separate source, requires auth; reserved for future expansion)
- IES grantee sites (separate source; reserved for future expansion)
- Individual student-level data (FERPA-protected; this wiki indexes metadata only)
- Resources discovered after 2026-04-27 scrape

## What a Querying Agent Should Expect

1. Read `llms-full.txt` to get all 74 entries in one request (recommended)
2. Or read `llms.txt` for an entry-level index, then fetch category files
3. Every entry has: title, type, URL (or AIMS fallback), tags, description
4. `description_inferred: true` signals agent-written descriptions not validated against source
5. `url_confirmed: false` signals URLs not directly verified during compilation

## Maintenance Model

Manual or semi-automated weekly rescrape of `aimscollaboratory.org/resources`.
New entries detected by comparing scraped titles against existing `llms-full.txt`.
Changed entries detected by SHA256 hash comparison of fetched page content.
