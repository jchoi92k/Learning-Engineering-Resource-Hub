# Repo Index — Renaissance AI and Education Resource Hub

> Map of the public repo. If you're new here (human or cold-starting Claude session), start with this file.

The hub is a **referatory** — a curated index of evidence-based K-12, higher-education, and learning-engineering resources, hosted at GitHub Pages and consumable by both humans and LLM agents (via `llms.txt` and an MCP server). It does not store source content; it stores metadata + descriptions and links out.

**Current state:** 1,181 indexed entries across 20+ sources (WWC, NWEA, Mathematica, WestEd, JEDM, LPI, EdTrust, and more). Coverage tracked in `docs/data.json` (`meta.coverage`) and `meta/source-targets.json`.

---

## Start here

| If you want to… | Go to |
|---|---|
| Browse the indexed resources (human UI) | `docs/index.html` — run `python -m http.server 8765` from `docs/` and open localhost:8765 |
| Consume the corpus as an LLM (full text) | `docs/llms-full.txt` |
| Consume the corpus as an LLM (compact) | `docs/llms.txt` |
| Understand entry format and tag schema | `docs/schema.md` |
| Understand scope and audience | `docs/purpose.md` |
| Add new entries from a known source | `meta/backlog-prompt.md` (run in Claude Code) |
| Onboard a brand-new source | `meta/new-source-prompt.md` (interactive; triggered from a `[New source]` GitHub issue) |
| Run the weekly all-source check | `meta/automation-prompt.md` (executes end-to-end; configured as a weekly cloud routine at claude.ai/code/routines) |
| Inspect past automated runs | `meta/automation-log.md` |
| Onboard a new Claude Code agent | `meta/agent-guide.md` |
| Understand deployment surfaces (Pages / MCP / Gem) and what needs manual deploy | `meta/operator-guide.md` |
| Check what's been done recently | `git log` |

---

## File map

### Root
- **`CLAUDE.md`** — project instructions loaded by every Claude Code session. Read first if you're an agent.
- **`README.md`** — human-facing repo description.
- **`index.md`** — this file.
- **`.gitignore`** — note: `private/` (internal docs, meeting notes, decision log, drafts) is gitignored.

### `docs/` — the published referatory
- **`llms-full.txt`** — primary file. All 1,181 entries with descriptions + auto-generated nav header. The canonical corpus.
- **`llms.txt`** — compact index (titles, URLs, types, tags — no descriptions).
- **`data.json`** — JSON view; consumed by `index.html`.
- **`index.html`** — human-facing UI (browse by tag, source, type).
- **`tags/`** — per-tag markdown files (auto-generated).
- **`schema.md`** — entry format, type taxonomy, full tag vocabulary.
- **`purpose.md`** — scope, audience, hosting notes.
- **`build_tags.py`** — parses `llms-full.txt`, regenerates header, generates `llms.txt`, `data.json`, and `tags/*.md`. **Run after every edit.**
- **`gem-knowledge.txt`** — generated artifact for the Gemini Gem.
- **`staging/`** — temporary working directory for subagent output; gitignored, cleared after each merge.

### `meta/` — operational docs and tooling
- **`agent-guide.md`** — master operational reference for cold-starting Claude agents. Entry format, tag schema, source URL patterns, current state, subagent protocol.
- **`operator-guide.md`** — how the four surfaces (GitHub Pages, MCP worker, Gemini Gem, llms.txt) are connected, what auto-updates vs. needs manual deploy, after-merge checklist, handoff notes.
- **`automation-prompt.md`** — self-contained prompt for the weekly automated source-check. Used by the scheduled cloud routine; does end-to-end discovery → stage → merge → build → commit → PR. Also runnable interactively from this terminal.
- **`automation-log.md`** — append-only run log; each weekly run adds one entry summarizing additions, drops, failures, and a link to the cloud session transcript.
- **`backlog-prompt.md`** — self-contained prompt for expanding coverage of a single source that already has some entries but a backlog remains.
- **`new-source-prompt.md`** — self-contained prompt for onboarding a brand-new source (scope check → access discovery → initial pass → canonical doc updates → PR). Run interactively after triaging a `[New source]` GitHub issue.
- **`inclusion-criteria.md`** — what qualifies for inclusion (source-level + resource-level rules).
- **`sources-inventory.md`** — full catalog of sources with access notes and URL patterns.
- **`source-audit.md`** — accessibility review of every source.
- **`sources-log.md`** — raw log of source-access attempts (what worked, what didn't, why).
- **`gem-instructions.md`** — instructions for the Google Gemini Gem (`gem-knowledge.txt` is its knowledge file).
- **`source-targets.json`** — coverage targets per source; consumed by `build_tags.py` to compute `meta.coverage`.
- **`playwright-scrape.py`** — scraper for JS-rendered sources (TNTP, Digital Promise). Usage: `python meta/playwright-scrape.py [tntp|digital-promise]`.
- **`source-check.py`** — pre-flight accessibility probe. Hits each source's discovery URL + a sample publication URL and classifies the result as OK / PARTIAL / DEGRADED / JS-RENDERED / BLOCKED. Run before a manual automation pass to see what's reachable: `python meta/source-check.py`. Note: maintains its own source list (drifts from `meta/source-targets.json` — refresh manually when adding sources).

### `worker/` — Cloudflare Worker (MCP server)
- Deployed at `https://renaissance-hub.joon-96a.workers.dev`. Exposes the hub via MCP so LLM agents can query it directly.

### `private/` — gitignored, not in this repo's public view
Holds the decisions log, meeting notes, internal strategy, research drafts, and positioning docs. See `private/index.md` (only readable locally).

---

## Common operations

```powershell
# Local human-facing UI
cd docs
python -m http.server 8765
# open http://localhost:8765

# Rebuild after editing llms-full.txt
cd docs
python build_tags.py

# Scrape a JS-rendered source
python meta/playwright-scrape.py tntp

# Deploy the MCP worker
cd worker
npx wrangler deploy
```

---

## Conventions

- **No inference.** Descriptions must come from fetched page content, never the title alone. Drop entries that 404 or 403.
- **UTF-8 only.** All files. `build_tags.py` validates and rejects mojibake.
- **Subagents write to files, not text.** Any agent collecting entries writes to `docs/staging/{source}.txt`. Data returned as agent text is lost on context compaction.
- **Staging → merge → build → commit.** After staging is reviewed, append to `llms-full.txt`, run `build_tags.py`, delete the staging file, commit.
- **Major decisions are logged.** Decisions go to `private/decisions.md` (append-only, newest at top). Do not edit historical entries; append a new one if reversing.
- **New md files get indexed.** Any new markdown file added to `meta/` is listed here in `index.md`. Anything added to `private/` is listed in `private/index.md`. Build/referatory artifacts (auto-generated files, scripts) don't need indexing.
