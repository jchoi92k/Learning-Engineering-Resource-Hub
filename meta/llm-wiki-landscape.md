# LLM-Facing Wiki Landscape

> How prominent knowledge hubs structure, serve, and connect themselves to LLMs — and where our hub fits.

---

## Overview of Patterns

Three distinct approaches have emerged for making knowledge accessible to LLMs. They differ in purpose, architecture, and how agents "plug in."

---

## 1. llms.txt Standard

**Origin:** Jeremy Howard (Answer.AI / fast.ai), proposed September 2024.  
**Canonical spec:** https://llmstxt.org/  
**Purpose:** Give LLMs a clean, structured entry point to a website — analogous to `robots.txt` for crawlers.

### Format

A plain Markdown file served at `/llms.txt` on the domain root:

```markdown
# Project Name

> One-paragraph summary of what this is and who it's for.

## Section Name
- [Page Title](https://example.com/page) — one-line description
- [Another Page](https://example.com/other) — description

## Optional Section
...
```

**Required:** H1 with site/project name.  
**Recommended:** blockquote summary, H2 sections with annotated links.

### Companion files

| File | Purpose |
|---|---|
| `/llms.txt` | Discovery layer — curated index of key pages |
| `/llms-full.txt` | Full content dump — entire site text in one Markdown file |
| `/{page}.md` | Per-page clean Markdown variants (URL + `.md`) |

The `llms-full.txt` convention was developed collaboratively between Mintlify and Anthropic. It enables a single WebFetch call to load the full knowledge base into context.

### Adoption (as of 2026)

Major adopters: Anthropic (Claude docs), Cloudflare, Vercel AI SDK, Stripe, Cursor, Perplexity, Hugging Face, ElevenLabs, CrewAI.  
Mintlify auto-generates llms.txt + llms-full.txt for all hosted docs sites.  
Tracked at: https://directory.llmstxt.cloud/ (2,000+ sites indexed across developer tools, AI, finance, products)

### Effectiveness caveats

- No major AI platform has officially confirmed they read these files at inference time.
- Google explicitly dismissed it for search.
- Primary value: token efficiency (up to 10x vs raw HTML) and deterministic agent navigation, not SEO.
- LangChain benchmarks: agents using llms.txt significantly outperformed vector search approaches for documentation tasks.

### How agents "plug in"

An agent is given the base URL. It fetches `/llms.txt` to discover the structure, then fetches `/llms-full.txt` for full context (or per-section files for targeted queries). No special tooling required — standard WebFetch.

---

## 2. Karpathy LLM Wiki Pattern

**Origin:** Andrej Karpathy, posted on X in April 2026. 16M+ views, 5,000+ GitHub stars within days.  
**Gist:** https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f  
**Purpose:** A persistent, LLM-maintained markdown knowledge base — not a webpage, but a living internal document the LLM reads and writes.

### Architecture

```
project/
├── raw/                  # Immutable source documents (PDFs, articles, notes)
├── wiki/
│   ├── index.md          # Catalog — every page with one-line summary, by category
│   ├── log.md            # Append-only changelog (date, operation, what changed)
│   ├── [entity].md       # One page per concept, person, project, etc.
│   └── [concept].md
└── CLAUDE.md / AGENTS.md # Schema: wiki structure, conventions, workflows
```

### Core operations

| Operation | What it does |
|---|---|
| **Ingest** | Process new source → update 10-15 wiki pages (extract, cross-reference, flag contradictions) |
| **Query** | Answer from wiki; file new insights as pages |
| **Lint** | Health checks: stale claims, orphaned pages, missing cross-references |

### Per-page metadata

Each wiki page includes frontmatter with: `type`, `source`, `dates`, `tags`, `confidence`, `backlinks`.

### How agents "plug in"

1. **CLAUDE.md directive:** `"Always check wiki/ before answering questions about this project's architecture, patterns, or decisions."` Without this, Claude won't proactively consult the wiki.
2. **SessionStart hook:** Auto-loads the first 60 lines of `wiki/index.md` and last 15 lines of `wiki/log.md` into every session.
3. **MCP integration (emerging):** Tools `wiki_search`, `wiki_ingest`, `wiki_lint` as MCP calls; wiki files as MCP resources.

### Philosophy

"The LLM doesn't get bored, doesn't forget to update a cross-reference." LLMs solve the maintenance burden that causes humans to abandon wikis. Echoes Vannevar Bush's Memex vision — finally with the maintenance layer Bush couldn't provide.

### Key distinction from RAG

No embedding models, no vector databases, no chunking strategies. A single inference call loads the entire wiki (works cleanly under ~100K words). Context window (200K tokens in Claude) replaces retrieval infrastructure.

---

## 3. Context7 (MCP Documentation Layer)

**Creator:** Upstash  
**Site:** https://context7mcp.com/  
**Repo:** https://github.com/upstash/context7  
**Purpose:** Dynamic, semantic documentation lookup for AI coding assistants — solves stale training data in code generation.

### Architecture

Context7 indexes 9,000+ software libraries. For each library, it:
1. Extracts code snippets and documentation
2. Enriches with explanations
3. Vectorizes for semantic search
4. Reranks with proprietary algorithms
5. Caches with Redis

Generates `llms.txt` for each indexed library, but adds dynamic search on top (unlike static llms.txt).

### MCP tools

| Tool | Purpose |
|---|---|
| `resolve-library-id` | Map a library name → Context7-compatible ID |
| `get-library-docs` | Fetch docs for a library, filtered by topic + token budget |

### How agents "plug in"

Via MCP server — the agent calls `resolve-library-id` and `get-library-docs` as tool calls. No URL memorization required. Integrates with Cursor, VS Code + Copilot, Claude, Windsurf.

### Distinction

Context7 is a queryable service on top of the llms.txt layer. llms.txt = static index; Context7 = dynamic retrieval with semantic ranking.

---

## 4. Knows / knows.academy

**Paper:** "Knows: Agent-Native Structured Research Representations" (April 2026) — arxiv:2604.17309  
**Hub:** https://knows.academy/  
**Purpose:** YAML "sidecar" specifications that coexist with research papers — structured claims, evidence, provenance, and verifiable relations in a form LLM agents can consume directly.

### Architecture

A KnowsRecord is a thin YAML file that accompanies an existing research paper. It encodes structured metadata about what the paper claims, with what evidence, and how claims relate to other work — without hosting any content. The community hub at knows.academy has indexed 10,000+ publications.

### Key empirical finding

From the paper (fetched and verified 2026-05-03 — see `docs/knows-2604.17309-summary.md` for full notes):

- **Weak models (0.8B–2B)**: 19–25% → 47–67% accuracy (+28–42 pp) reading YAML sidecar vs. full PDF
- **29–86% fewer input tokens** depending on model
- **Statements-only variant**: 93% fewer tokens vs. PDF, retaining 88% of full-sidecar accuracy (12.7× token efficiency)
- **Medium/strong models**: gains are discipline-dependent, not consistent — the headline story is specifically about weak models

Important caveats: (1) both sidecars and benchmark questions were authored by Claude Opus — circular evaluation bias; (2) the ~7-statement template used in the main evaluation underestimates optimal performance by up to 57 pp (per E9 ablation); (3) tested on 20 classic papers only.

### Similarity to our hub

| Dimension | Knows | Our hub |
|---|---|---|
| Format | YAML per entry | YAML frontmatter per entry |
| Content hosting | No — metadata only | No — links + metadata |
| Primary consumer | LLM agents | LLM agents |
| Domain | ML/science | Education research |
| Scale | 10,000+ | 569 |
| Hosting | Centralized community hub | Self-hosted local + ngrok |

**Knows is a sidecar** (attached to existing publications); our hub is standalone. Knows accompanies papers at their source URLs; our hub indexes across organizations. Different implementation, same underlying pattern.

### Why it matters

Knows is the closest known project to our hub, and it was published as a formal research paper validating the design. Our architecture is not a one-off — it is an independently-arrived-at instance of an emerging standard for agent-native knowledge representation.

---

## 5. AI Policy Hub (Will Rinehart / AEI)

**Site:** https://policyhub.us/  
**Creator:** Will Rinehart, American Enterprise Institute  
**Built on:** Docusaurus (static site generator — `/docs/` URL structure, sitemap-confirmed)  
**Purpose:** Centralized tracking of AI policy across state, federal, and executive levels.

### Structure (41 pages, reviewed 2026-05-01)

| Section | Content |
|---|---|
| State AI Bills | Interactive map + dropdown + weekly update table |
| Federal AI Bills | Bill tracker |
| Executive Actions | Monitoring section |
| Official Datasets | Census + government data links |
| Economic Trends | DataWrapper visualizations |
| Readings / Reports | ~100 curated resources across 9 flat categories |
| Toolkit | Regulatory frameworks for policymakers |
| My AI Work | Rinehart's own research |

### Resource metadata (readings/reports section)

Each entry has: title (linked), brief description (1–3 sentences).  
Inconsistently present: author/organization, publication date.  
Absent: type field, tags, machine-readable structure.

### Update cadence

Weekly manual updates to legislative tracking tables. No automated pipeline.

### LLM integration

**None.** `/llms.txt` returns 404. `/llms-full.txt` returns 404. No JSON data layer, no API, no structured metadata. Pure human-browsing HTML.

### Key takeaway

Will built an excellent human-facing referratory. The LLM-agent-facing dimension is Proposer's own addition to the concept — Will's hub does not do this. Our hub already has the LLM-facing architecture Will's lacks; the gap is scope (LE-only vs. AI policy broadly) and public hosting.

---

## Comparison Table

| Characteristic | llms.txt standard | Karpathy Wiki | Knows / knows.academy | Context7 | AI Policy Hub | **Our Hub** |
|---|---|---|---|---|---|---|
| **Purpose** | Web discoverability | Personal/project knowledge | Research metadata sidecars | Code docs | Policy tracking | LE resource index |
| **Primary consumer** | LLM agents (WebFetch) | LLM agents (context window) | LLM agents | AI code editors (MCP) | Humans only | LLM agents (WebFetch) |
| **Entry point** | `/llms.txt` | `CLAUDE.md` directive | Per-paper YAML sidecar | MCP server install | Navigation menu | `/llms-full.txt` (self-contained) |
| **Full content fetch** | `/llms-full.txt` | Load wiki/ directory | Community hub index | `get-library-docs` | ✗ none | `/llms-full.txt` ✓ |
| **Content format** | Clean Markdown | Markdown (LLM-generated) | YAML per entry | Vectorized + ranked | HTML (human) | Markdown flat files ✓ |
| **Metadata per entry** | Link + description | Frontmatter (type/tags/confidence/backlinks) | YAML (claims/evidence/provenance) | Version + topic | Title + URL + partial description | YAML frontmatter ✓ |
| **Tag / category nav** | H2 sections | index.md catalog | Claim types | Library ID | Flat categories (no tags) | tags/ + by-domain/ ✓ |
| **JSON data layer** | No | No | No | Yes (vectorized) | No | `data.json` ✓ |
| **Auto-update** | Site-owner dependent | LLM ingest pipeline | Community contributions | Continuous (Upstash) | Manual weekly | Manual ✗ |
| **Change log** | None | `log.md` (append-only) | None | Version-pinned | None | None ✗ |
| **MCP integration** | No | Emerging | No | Core feature | No | Cloudflare Worker ✓ |
| **Human-facing layer** | Parent website | None | knows.academy UI | Context7 UI | Docusaurus site | `index.html` + `data.json` ✓ |
| **Schema / field definitions** | None | `CLAUDE.md` (required) | KnowsRecord spec | N/A | None | `schema.md` + `purpose.md` ✓ |
| **Hosting** | Domain root (static) | Local files | Cloud (centralized) | Cloud (Upstash) | Docusaurus / static | GitHub Pages (public) |
| **Empirical agent accuracy** | Not measured | Not measured | Weak models: 47–67% vs. 19–25% on PDF (gains inconsistent for mid/strong models; circular eval bias — see summary doc) | Not published | N/A | Not measured |

---

## How LLM-Facing Wikis Get "Plugged In"

There are four integration models in practice:

### 1. URL-based (what we use)
Share a URL with the agent. The agent fetches `/llms-full.txt` which contains all entries with a navigation header. Single file, no multi-file navigation required — critical because chat-based LLMs (Claude.ai, ChatGPT) cannot follow URLs discovered inside fetched content.

**How to tell an agent:** *"Read this first: [url]/llms-full.txt — it's a full index of learning engineering resources."*

**Our implementation:** GitHub Pages (public). Confirmed working with Claude web UI. See "LLM Fetch Restrictions" section below for constraints discovered during testing.

### 2. Context window injection (Karpathy pattern)
Wiki files are loaded directly into the context window at session start via a SessionStart hook or by manually pasting content. No WebFetch required.

**How to tell an agent:** CLAUDE.md directive + SessionStart hook auto-loads index.md and log.md.

**Our implementation:** Not implemented. Could add via `docs/llms-full.txt` + CLAUDE.md directive.

### 3. MCP server (Context7 model)
The wiki is exposed as MCP tools. The agent calls `wiki_search(query)` or `wiki_get(entry_id)` as structured tool calls, without needing to fetch raw files.

**How to tell an agent:** MCP server is installed in the agent's environment; tools appear automatically.

**Our implementation:** ✓ Done. Cloudflare Worker at `https://le-resource-hub.joon-96a.workers.dev/mcp` with four tools: `search_resources`, `list_tags`, `get_entry`, `get_full_index`. Streamable HTTP transport, compatible with Claude Code, Cursor, Windsurf, Codex. Config: `.mcp.json` with `"type": "http"`. The `get_full_index` tool enables 1M+ context models to load the entire corpus in one call.

### 4. Search-indexed (OpenAI / Perplexity web browsing)
The wiki is publicly hosted with proper SEO and llms.txt, so agents with web search can find it via search queries.

**How to tell an agent:** Nothing — the agent finds it through search.

**Our implementation:** GitHub Pages is live. Not yet confirmed whether search engines have indexed the site.

### 5. Platform-hosted chatbot (Gemini Gem / ChatGPT GPT)
The knowledge base is uploaded to a platform that handles RAG retrieval internally. Users interact via a shared link — no file fetching, no URL construction, no truncation.

**How to tell a user:** Share the Gem/GPT link. They click it and start asking questions.

**Our implementation:** Gemini Gem with `data.json` upload. Instructions in `meta/gem-instructions.md`. Public sharing = zero friction. See "Delivery Platforms" section below for full comparison.

---

## What Our Hub Does Well

1. **llms-full.txt format:** Correct — single fetch loads all 569 entries with full metadata and auto-generated navigation header.
2. **Self-contained design:** No cross-file references in llms-full.txt. Header includes tag directory, source/type summaries, and usage instructions. Agent never needs to fetch a second file.
3. **Schema documentation:** `schema.md` and `purpose.md` give agents explicit field definitions and provenance rules.
4. **Tag navigation:** 66 per-tag files generated for the web UI and for agents with multi-file fetch capability.
5. **Dual layer:** Human-facing (`index.html` + `data.json`) + LLM-facing (flat files) coexist cleanly.
6. **Metadata density:** YAML frontmatter with `url_confirmed`, `description_inferred`, `type`, `source`, `tags` per entry.

## Gaps vs. Best Practice

| Gap | Best practice | Effort to close |
|---|---|---|
| No `log.md` | Append-only changelog (Karpathy) | Low — add file, update on each build |
| No CLAUDE.md directive | SessionStart hook + directive | Low — add to CLAUDE.md |
| No auto-update | Weekly ingest pipeline | High — OpenAlex API + GitHub Actions |
| No MCP server | Context7 model | ✓ Done — Cloudflare Worker with 4 tools (search, list_tags, get_entry, get_full_index) |
| No public URL | GitHub Pages or similar | ✓ Done — GitHub Pages live |
| Chat agent truncation | Platform-hosted chatbot | ✓ Done — Gemini Gem (data.json upload) |
| No per-entry confidence | Karpathy frontmatter | Low — add `confidence` field to schema |
| No backlinks | Cross-reference tracking | Medium — rebuild step in build_tags.py |

---

*Research compiled 2026-05-01 (landscape), 2026-05-03 (scaling, Knows/knows.academy, LLM-native architecture). Sources: llmstxt.org, Karpathy gist, Upstash/Context7, policyhub.us, Mintlify blog, llmstxt.cloud directory, OpenAlex (arxiv:2205.01833), Hugging Face Datasets docs, AI2 OpenScholar blog, Knows (arxiv:2604.17309), Papers With Code, VentureBeat/Karpathy coverage.*

---

## Scaling Architecture

> Added 2026-05-03. Context: hub reached 487 entries (~7,000 lines in llms-full.txt); user asked for field standards on scaling a discovery index before deciding on architecture changes. User has a solution in mind — this section documents the research to validate it.

### The flat-file ceiling

Our current source of truth is `llms-full.txt` — a single Markdown file with all entries. This works well under ~500 entries: fast single-fetch, no query layer needed, transparent git diffs. At larger scales the problems compound:

| Scale | Approx. lines | Issues |
|---|---|---|
| 500 entries (current) | ~7,000 | None significant |
| 2,000 entries | ~29,000 | Slow token load; large context cost for agents |
| 5,000 entries | ~72,000 | Exceeds practical single-context fetch; painful manual edits |
| 10,000+ | ~144,000+ | Context window overflow; diff noise on any build |

Separately: agents that fetch `llms-full.txt` to answer a narrow question pay the full token cost regardless. A query interface changes the economics.

### How reputable projects handle scale

| Project | Scale | Source of truth | Export format | Discovery layer |
|---|---|---|---|---|
| **OpenAlex** | 209M works | Database (REST API, updated daily) | Biweekly flat-file JSON dumps | REST API + bulk download |
| **Context7** | 33,000+ libraries | Vector database (Upstash Vector) | Per-library llms.txt files | MCP tool calls (`get-library-docs`) |
| **Hugging Face Datasets** | 12 PB | Git + LFS (version-controlled flat files) | Parquet/JSON per dataset | Dataset Hub API + direct download |
| **AI2 OpenScholar** | 45M papers | Custom retrieval datastore | Open data dumps + retrieval index | Retrieval-augmented pipeline |
| **llms.txt spec** | 12,000+ adopters | Parent site CMS/database | Generated llms.txt on each build | Static file at `/llms.txt` |

**The consistent pattern:** At scale, the *source of truth* shifts to a database or structured store; flat files become *generated exports*, not the canonical editing surface. Nobody edits the OpenAlex JSON dump files directly — those are read artifacts produced by a build.

Hugging Face is the notable exception: they deliberately chose version-controlled flat files (Git + LFS) over a traditional database to preserve transparency and ease of use. But their per-dataset unit is a structured `dataset_card.md` file — not a monolithic concatenated file. The "flat file source of truth" pattern they use is per-item files, not one growing flat file.

### Two different questions: general scaling vs. LLM-native scaling

The initial version of this section (2026-05-03) answered the general software-engineering question: how do reputable structured data projects scale? Answer: flip the source of truth from a growing flat file to per-item files or a database as early as practical.

A follow-up question asked the right framing: **does the answer change when LLMs are the primary consumer?** Research into Knows/knows.academy (arxiv:2604.17309) and the Karpathy wiki pattern says yes — for LLM-native consumption, the recommendation is *less* complexity, not more.

### Why LLM-native changes the calculus

RAG and database-backed APIs were designed for 4K–8K token context windows. At Claude's 200K context window, a 487-entry `llms-full.txt` (~150–200K tokens) fits in a single fetch. An agent can load the full file and reason over it without any retrieval infrastructure. The Karpathy pattern explicitly frames this as the obsolescence of RAG for sub-1,000-entry knowledge bases.

The Knows paper validates the metadata format directly: structured YAML per entry improves agent accuracy 2–3x over unstructured text while consuming 29–86% fewer tokens. Our current YAML frontmatter is already aligned with this.

### Options for our hub (LLM-native framing)

| Option | Description | Appropriate at | Complexity |
|---|---|---|---|
| **A — Stay flat** | Single `llms-full.txt`, full-file WebFetch | Current → ~800 entries | None |
| **B — Shard by source** | `llms-wwc.txt`, `llms-jedm.txt`, etc.; master index | ~800–5,000 entries | Low |
| **C — MCP query layer** | MCP tools wrapping `data.json` (`search_resources`, `list_tags`, `get_entry`, `get_full_index`) | ✓ Deployed on Cloudflare Workers | Done |
| **D — Per-entry files (general standard)** | Individual `entries/0488.yaml`; flat files generated | Multi-editor or programmatic-write use case | Medium |
| **E — Vector DB / RAG** | Semantic search at query time | 5,000+ entries | High |

### Field standard conclusion (revised for LLM-native)

**For a 487-entry LLM-native hub, the current flat-file architecture is correct.** Options B and C are the right evolution path:

1. **Stay on `llms-full.txt` through ~800 entries.** No changes needed now.
2. **Plan source-sharding at ~800 entries.** The structure already exists implicitly — entries are organized by source. When approaching the ceiling, split into per-source files with a master index listing shard names, entry counts, and topic tags.
3. **Add an MCP query tool when interactive supervised use grows.** A lightweight MCP wrapper over `data.json` with `filter_by_tag` / `filter_by_source` tools enables query-like access without a database.
4. **No vector embeddings until 5,000+ entries.** RAG overhead is unjustified below that threshold with a 200K context window.

Option D (per-entry files as source of truth) is the right call for general software projects or multi-editor workflows — but it adds editor complexity without any agent-facing benefit. The generated `llms-full.txt` is what agents consume; how it is produced is invisible to them.

### General scaling notes (for reference)

The general software-engineering standard (from OpenAlex, Hugging Face, AI2): flip the source of truth as early as practical. Projects that started as growing flat files faced painful migrations at 10K–50K entries. The Hugging Face lesson: "version-controlled flat files" works — but only when the unit is *per-item files* in git, not a monolithic concatenated file. Both principles apply if this hub ever becomes a multi-editor project or needs to support programmatic writes at scale.

### Conversation context (2026-05-03)

Two concerns raised: (1) coverage asymmetry (WWC dominating one category) — a sampling artifact solvable by expanding other sources, not an architecture problem; (2) flat file scaling ceiling — a real concern, but the LLM-native framing pushes the relevant threshold to ~800 entries, not ~500.

User has a solution in mind. No changes made yet — architecture decision pending user direction.

---

## Decided Architecture (2026-05-04)

### Dual-track delivery

Two parallel access patterns for the same corpus:

**Full track** — entries with complete YAML + description paragraph:
- `llms-full.txt` — all entries concatenated (generated; backward-compatible for agents fetching the full corpus)
- `llms-[source].txt` — per-source shards (`llms-wwc.txt`, `llms-datasets.txt`, etc.) for agents that know which source they want

**Lean track** — entries with YAML only, no description paragraph:
- `llms-lean-[category].txt` — per-domain-tag files (`llms-lean-math.txt`, `llms-lean-literacy.txt`, etc.) for agents scanning many entries cheaply before deciding what to fetch in full

Grounded in the Knows paper (arxiv:2604.17309) statements-only ablation: stripping descriptions retains 88% of navigational utility at 12.7× better token efficiency.

### Per-entry fragment files as source of truth

Individual fragment files replace `llms-full.txt` as the editing surface:

```
entries/
  wwc/         0001.md  0002.md  ...   (one file per entry)
  lpi/         0138.md  ...
  edtrust/     0145.md  ...
  datasets/    0387.md  ...
  ...

docs/
  llms-full.txt          ← generated by build script
  llms-wwc.txt           ← generated
  llms-lean-math.txt     ← generated (lean transform: strip description)
  llms.txt               ← master index; updated by build script
  data.json              ← generated by build_tags.py
  tags/                  ← generated
  build_tags.py          ← updated to read from entries/ + produce all outputs
```

`llms-full.txt` and all shard/lean files are **generated outputs**, committed to the repo so agents and GitHub Pages can fetch them as static URLs without a build step running server-side.

### GitHub limits confirmed (2026-05-04)

- No total-repo file count limit
- Hard limit: **3,000 entries per directory** (from docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)
- Solution: source-bucketed subdirectories under `entries/` — each stays well under 3,000 even at full indexing scale

### Subagent staging protocol update

With per-entry fragment files, subagents write individual files to `docs/staging/entries/` (e.g., `001.md`, `002.md`) instead of a single staging `.txt`. No absolute-numbering coordination during collection. Build script assigns final IDs when promoting staging → entries.

### GitHub Pages (next step)

See GitHub Pages checklist in `meta/indexing-decisions.md`.

---

## LLM Fetch Restrictions (discovered 2026-05-06)

> Critical constraint discovered during live testing with Claude.ai. Invalidated the hub-and-spoke architecture.

### The problem

Chat-based LLM agents (Claude.ai, ChatGPT) have a fetch policy restriction: **they can only fetch URLs the user directly pastes in their message or URLs that appear in web search results.** They cannot follow URLs discovered inside fetched content.

This means:
- User pastes `llms.txt` URL → agent fetches it → sees tag file URLs in the content → **cannot fetch them**
- The hub-and-spoke architecture (llms.txt → tag files → llms-full.txt) is broken for chat agents
- The one file the user pastes must be self-sufficient

### What was tested

1. **llms.txt (128KB, ~32K tokens)** — loaded successfully ("The index file loaded"), but agent immediately tried to follow links to llms-full.txt and tag files, failed, and got confused
2. **llms-full.txt (484KB)** — partially loaded in earlier test (~487 of 569 entries); agent got confused by header referencing other files
3. Agent hallucinated "v2 curation policy" and "legacy file" references that don't exist in the content — likely from partial truncation + web search noise

### What was considered and rejected

| Approach | Why rejected |
|---|---|
| Hub-and-spoke (llms.txt → tag files) | Chat agents can't follow URLs in fetched content |
| "Ask the user to paste tag URLs" | Terrible UX |
| llm-min.txt compressed format (SKF) | Zero empirical benchmarks proving LLMs perform well reading it; requires companion guideline file (same fetch restriction); adoption nonexistent |
| Slim llms.txt (~10KB navigation only) | Loses descriptions, which are the actual value-add |

### What we landed on

**llms-full.txt as the single self-contained entry point** with an auto-generated compact header:

- ~19 lines of comment-prefixed metadata: tag directory (by category), type breakdown, source list with counts, usage instructions
- Explicit instruction: "Do NOT attempt to fetch other files. This file is self-contained."
- No references to llms.txt, tag files, schema.md, or any other file
- Header is auto-generated by `build_tags.py` (`build_full_header()` function) on every build — stays in sync with entry data

**llms.txt retained** as a compact index (titles, URLs, types, tags — no descriptions) for tools with multi-file fetch capability or strict size limits. Not the recommended entry point.

### Why this works

1. **Single file = zero navigation needed.** No permissions problem.
2. **Frontloaded header = graceful degradation.** Even if the tail gets truncated, the LLM has the tag directory and source map. It knows what it's missing.
3. **Chat agents paginate.** Claude.ai read ~487 entries from the file in testing — it gets through most of the content, just may not get all of it.
4. **URLs in chat is natural UX.** The LLM presents matching entries with clickable URLs. The user clicks. Standard chat behavior.

### Implication for the "Decided Architecture" above

The dual-track + per-entry fragment architecture (decided 2026-05-04) remains the right scaling plan for the source of truth. But the **delivery layer** is now simplified: llms-full.txt is the single recommended fetch target, and its header must be self-contained with no cross-file references. The lean track and per-source shards are deferred until there's evidence that API-based or MCP-based agents (which CAN navigate between files) become significant consumers.

### Research finding: llms-full.txt is what agents actually fetch

Mintlify's CDN analysis (documented in hub-design-notes.md) found llms-full.txt receives 3–4x more visits than llms.txt, with ChatGPT driving most traffic. This independently validates the decision to make llms-full.txt the primary entry point. LLMs prefer loading complete content in one request rather than navigating selectively.

---

## Delivery Platforms for Chat-Based Access (researched 2026-05-06)

> Context: llms-full.txt works for programmatic LLM agents but truncates at ~25% when fetched by chat agents (Claude.ai, ChatGPT). The Cloudflare Worker API works technically but chat agents can't construct query URLs. A platform that ingests the full knowledge base and exposes it via a shareable chatbot link solves both problems.

### Platform comparison

| Platform | Creator cost | How it works | Recipient friction | File limits | RAG? |
|---|---|---|---|---|---|
| **Gemini Gems** | Gemini Advanced/Pro | Upload files + write instructions | Zero (public mode = no sign-in) | 10 files, 100MB each | Yes |
| **ChatGPT Custom GPTs** | Plus ($20/mo) | Upload files + write instructions | Free ChatGPT account | 20 files, 512MB each, 2M tokens | Yes |
| **Poe** | Free | Upload files + write instructions | Poe account required | Varies by model | Yes |
| **Coze** | Free | Upload files + write instructions | Account (store) or anonymous (embed) | Varies | Yes |
| **Claude Projects** | Pro ($20/mo) | Upload files + system prompt | Org members only | 200K context window | Full context (not RAG) |

### Architecture differences that matter

**RAG platforms (Gems, GPTs, Poe, Coze):** Knowledge files are semantically indexed. The model receives only retrieved chunks per query, not the full file. This means:
- Large files (503KB+) are handled fine — no truncation
- Retrieval quality depends on file format: JSON > Markdown > PDF for structured data (Source: Medium benchmark, "MD vs JSON for GPT Knowledge Bases")
- The model may miss entries if the semantic search doesn't match — silent failure mode
- Anti-hallucination instructions are critical: without them, the model falls back to training data when retrieval returns empty (Source: concret.io, "Fix Gem Hallucinations")

**Full-context platforms (Claude Projects):** The entire knowledge base is loaded into the context window every turn. No retrieval step. This means:
- Perfect recall — the model sees every entry
- Limited by context window size (~200K tokens ≈ ~150K words ≈ ~500KB text)
- Our data.json at 557KB is right at the boundary — may need trimming
- No sharing outside the org

### Why Gemini Gems was selected

1. **Zero incremental cost.** User has Gemini Pro through org.
2. **Zero recipient friction.** Public sharing mode: share a link, anyone uses it, no sign-in.
3. **557KB data.json fits easily.** Well under the 100MB per-file limit.
4. **Google Drive integration.** Future: put data.json in Drive, Gem auto-updates when the file changes.
5. **Instruction-first architecture.** Instructions are always in context (not RAG-gated). Tag taxonomy, source list, and anti-hallucination rules are always visible to the model.

### Known Gems limitations

- **RAG retrieval can miss entries.** Semantic search may not match entries whose descriptions don't use the user's exact terminology. Mitigation: instructions include the full tag taxonomy so the model can translate user intent → tag names → targeted search.
- **January 2026 regression.** Users reported Gems ignoring uploaded documents entirely (Google Support thread #404592328). Status unclear — test during setup.
- **No programmatic access.** Gems are chat-only. For API/MCP consumers, the Cloudflare Worker or a future MCP server remains the right delivery mechanism.
- **File upload, not live sync (yet).** Google Drive integration exists but reliability varies. Manual re-upload on each build_tags.py run is the safe default.

### ChatGPT GPTs as secondary channel

GPTs have a larger ecosystem and longer track record for knowledge-base bots. If setting up a GPT as a secondary access point:
- Upload `data.json` (same file)
- GPT instructions can be adapted from `meta/gem-instructions.md` with minor adjustments
- Recipients need a free ChatGPT account (most already have one)
- GPTs support 20 files and 512MB — more headroom for future growth

### Instruction engineering findings (cross-platform)

Best practices verified through research (sources in indexing-decisions.md):

1. **Critical info in instructions, not just knowledge files.** Instructions are always in context; knowledge files are behind RAG. Tag taxonomy, response format, and anti-hallucination rules go in instructions.
2. **Anti-hallucination rules at start AND end.** LLMs attend most to the beginning and end of instructions (primacy/recency effect). The "never fabricate" rule appears twice.
3. **JSON > Markdown for structured catalogs.** Key-value format gives the retrieval engine better anchor points for structured data.
4. **Verbatim for specifics, summarize for context.** URLs, titles, and descriptions should be quoted exactly. Surrounding synthesis can be the model's own words.
5. **Explicit "not found" instruction.** Without it, both Gems and GPTs silently fall back to training data when retrieval fails.
