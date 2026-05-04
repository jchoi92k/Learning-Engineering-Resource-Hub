# Hub Maintenance Options

> How do we keep the hub growing and accurate without it becoming a manual grind?
> Compiled 2026-05-01 from discussion of the Karpathy LLM Wiki pattern and our specific constraints.

---

## Our constraint

This hub is a **referratory** — it links to externally-hosted resources and stores metadata + descriptions.
It does not download, host, or mirror source documents.

This rules out the full Karpathy LLM Wiki pattern as-is. That pattern's `raw/` folder holds downloaded PDFs
that the LLM reads before writing wiki pages. We don't want file storage, and many of our sources are
gated, paywalled, or require institutional access anyway.

The relevant part of the Karpathy pattern: LLM-assisted synthesis and structured metadata maintenance.
The irrelevant part: local document storage, full-text ingestion.

---

## The real question

Not "how do we maintain a wiki" but:
**how do we add entries and keep metadata accurate without it becoming a manual chore at scale?**

---

## Option A — Stay manual, reduce friction

No automation. Add small improvements that make manual entry-writing faster:

- **Entry template + Claude prompt:** paste a URL, Claude fetches and writes the YAML block + description
- **`log.md`:** append-only changelog — date, what was added/changed, by whom
- **`python add_entry.py <url>`:** wrapper that appends the entry and auto-runs `build_tags.py`

**When to use:** under ~150 entries; team is small; quality control is the priority.

**Upside:** zero infrastructure, zero new failure modes, full human control.

**Downside:** doesn't scale; the per-entry work is constant regardless of how many you've already done.

**Hallucination risk:** low — human writes or reviews every entry before it lands.

---

## Option B — URL-based LLM-assisted ingest (no file downloads)

The ingest step does a WebFetch on the source URL, summarizes the page, and writes a formatted entry.
Source document stays at its URL — we only store metadata + derived description in `llms-full.txt`.

This is what we already do manually. Automating it means:

```
python ingest_url.py https://example.com/paper
```

The script:
1. WebFetches the URL
2. Calls Claude API: "Given this page content, write a wiki entry in this YAML format: ..."
3. Appends entry to `llms-full.txt` with `url_confirmed: true`, `description_inferred: true`
4. Runs `build_tags.py` to regenerate tags/ and data.json
5. Appends a line to `log.md`

Human reviews the output before committing. Or runs in a batch and spot-checks.

**When to use:** right now — this is the natural next build step.

**Upside:** natural fit for a referratory; no storage; audit trail = the source URL itself; automatable in one session.

**Downside:** pages behind logins or paywalls return little useful content (same problem we have now).

**Hallucination risk:** medium — LLM summarizes what's actually on the page, but can misread or omit.
Mitigated by: `description_inferred: true` flag, human spot-check of generated entries.

---

## Option C — Scheduled source monitoring + human approval gate

Automated job checks known sources weekly for new items, flags candidates, human approves, LLM writes entries.

**Sources to monitor:**
| Source | Method | Cadence |
|---|---|---|
| AIMS Collaboratory resources page | Scrape + diff vs existing entries | Weekly |
| OpenAlex API | Query: learning engineering, ITS, formative assessment | Weekly |
| CoSN publications | RSS or page scrape | Weekly |
| TLA blog / publications | RSS | Weekly |
| learningengineering.org | Page scrape | Monthly |

**Workflow:**
1. Script runs → new items land in `queue.md` as "pending review"
2. Human reviews queue (5 min weekly): approve / reject / flag for more info
3. On approval, LLM fetches URL → writes entry → appends to `llms-full.txt`
4. `build_tags.py` runs → tags/ and data.json regenerate
5. Commit

**When to use:** when the hub has enough sources to justify the monitoring pipeline; when the team wants Proposer's "auto-updating" vision.

**Upside:** scales well; matches Will Rinehart's weekly refresh model; human stays in loop for quality, not discovery.

**Downside:** requires building the monitoring pipeline (OpenAlex API is well-documented and free; scraping AIMS is fragile). Meaningful build scope — separate project from the hub itself.

**Hallucination risk:** same as Option B. Monitoring step adds no new risk; it just automates discovery.

---

## Recommendation

**Option B now, Option C later.**

Option B is a one-session build. It reduces the per-entry manual work immediately and fits our current workflow.
Option C is the right long-term vision for Proposer's auto-updating goal, but it's a separate project with real scope.

The two are compatible: Option B's `ingest_url.py` becomes the write step inside Option C's pipeline.

---

## Why the full Karpathy pattern doesn't fit (summary)

| Karpathy pattern | Our situation |
|---|---|
| `raw/` folder with downloaded PDFs | No file downloads — we're a referratory |
| LLM reads full document text | Most sources are gated or paywalled |
| Wiki pages = LLM-synthesized summaries | Entries = metadata + short description; synthesis is not our goal |
| Self-maintaining (LLM updates cross-references) | build_tags.py already handles tag regeneration |
| SessionStart hook loads wiki into context | llms-full.txt already serves this function for external agents |

The Karpathy pattern is the right model for a **personal research wiki** (e.g., summarizing papers you've read).
Our hub is a **public-facing index** where the source of truth is the external URL, not a local document.

---

---

## The core format decision (added 2026-05-01)

Before choosing a maintenance approach, there's a more fundamental question:

**Is this hub a referratory or a knowledge base?**

| | Referratory (current) | Synthesized wiki (Karpathy pattern) |
|---|---|---|
| Stores | Links + metadata + short descriptions | LLM-written synthesis pages |
| Answers | "What resources exist on X?" | "What does the field say about X?" |
| Analogy | Card catalog | Encyclopedia |
| Source of truth | The external URL | The wiki page itself |
| LLM role | Reader at query time | Author at ingest time |
| Ownership / accuracy risk | Low — metadata is verifiable | Higher — synthesis reflects your interpretation |

Both are valid. Both use LLMs as a librarian. They answer different questions.

**For Proposer/Stakeholder to align on:** Is this hub meant to be a *directory* or a *knowledge base*?
- A practitioner asking "what tools exist for formative assessment?" → referratory
- A practitioner asking "what does the evidence say about formative assessment effectiveness?" → synthesized wiki

These can coexist: referratory entries in `llms-full.txt`, synthesis pages in a separate `synthesis/` directory.
That's the mature form of the Karpathy pattern applied to a field-facing resource hub.

---

## Real implementations of the Karpathy pattern (as of 2026-05-01)

The pattern is ~6 weeks old. The ecosystem is nascent.

**Most polished:**
- [nashsu/llm_wiki](https://github.com/nashsu/llm_wiki) — full desktop app (React + Tauri, macOS/Windows/Linux), knowledge graph with community detection, incremental wiki building. **Requires file imports — no URL-only mode.**
- **wuphf** — Git-tracked wiki, AI commits under "Pam the Archivist" identity, BM25 search, contradiction detection. Production-grade but no public URL or repo link found.

**Claude Code / agent skill wrappers:**
- [lucasastorian/llmwiki](https://github.com/lucasastorian/llmwiki) — MCP-based, upload docs, Claude writes wiki
- [SamurAIGPT/llm-wiki-agent](https://github.com/SamurAIGPT/llm-wiki-agent) — simple CLI wrapper
- [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) — Claude Code Agent Skills compatible

**The polished hosted app hasn't shipped yet.** All current implementations require local setup.

**Bottom line for our hub:** none of these fit directly. They're all built around local document ingestion. Our use case (URLs, no file storage, field-facing) isn't a primary target for any of them yet.

---

---

## Option D — Staging-based parallel collection + PR gate (validated 2026-05-01)

This is the pattern we now use and have validated at scale (110 entries added in one session):

**Concept:** Spawn parallel collection agents, each writing to a dedicated staging file. After all complete, a merge step renumbers and appends to `llms-full.txt`. Open a PR for human review before merging to main.

**Workflow:**
1. Assign each source a staging file (`docs/staging/{source}.txt`) and entry number range
2. Each agent: fetches listing/sitemap → fetches individual pages → writes formatted entries to its staging file as it confirms them
3. Main agent: reads staging files, renumbers to absolute positions, appends to `llms-full.txt`, runs `build_tags.py`
4. Human reviews diff in PR → approves → merges

**Why staging files matter:** Data returned as agent text is lost on context compaction. Files persist across compaction boundaries, making long parallel runs safe.

**GitHub Actions translation:**
- Cron trigger (weekly or on-demand)
- One job per source: fetches listing → diffs against known URLs in `llms-full.txt` → for new URLs, calls Claude API with the entry format prompt → writes to staging file
- Merge job: runs after all source jobs complete, renumbers, appends, runs `build_tags.py`
- PR opened automatically; human approves

**Known constraint:** Sequential entry numbers create a write conflict if two runs try to append simultaneously. Fix: serialize merge step, or switch to content-addressed IDs (UUID or URL-hash). Not a blocker at current scale.

**What needs to be built for full automation:**
- `scripts/discover_new.py {source}` — fetches source listing, returns URLs not yet in `llms-full.txt`
- `scripts/ingest_url.py {url}` — fetches URL, calls Claude API, writes formatted entry to stdout (or staging file)
- GitHub Actions `.yml` wiring the above with cron + PR creation
- `ingest_url.py` is essentially Option B's script — build it first

**Hallucination risk:** Same as Option B. Tag assignment quality may drift without human review. Mitigated by: PR gate, `description_inferred` flag, spot-checking.

---

## Related docs

- `meta/llm-wiki-landscape.md` — full landscape analysis (llms.txt, Karpathy, Context7, Policy Hub)
- `docs/purpose.md` — scope and maintenance model
- `build_tags.py` — current build step (generates tags/, data.json)
