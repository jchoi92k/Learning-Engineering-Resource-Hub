# Agent-Facing Wiki: What It Actually Means

---

## The Core Distinction

"Agent-facing" means the primary consumer is an LLM agent, not a human browser.
This is not just a format change — it inverts the design priorities:

| Human-facing library | Agent-facing wiki |
|---|---|
| Search/filter UX | Explicit index the agent reads first |
| Rich metadata display | Dense, self-describing content |
| Pagination | Flat files or hierarchical indexes |
| Auth walls, login flows | Unauthenticated, stable URLs |
| Discovery via search engine | Discovery via llms.txt or direct URL |
| Formatted for skimmability | Formatted for full consumption |
| Updated by humans | Can be maintained by an agent |

---

## What Format Actually Works

### The user's instinct: "a JSON hosted on a page could technically work"

Yes, and for the *index/catalog layer* it's probably right. But JSON alone has a
problem: it's good for structured fields, bad for the prose that explains *why*
a dataset matters, what its quirks are, what it's been used for. That context is
what makes a wiki useful rather than just a metadata dump.

The practical answer is a hybrid:

**YAML/JSON frontmatter** — structured, machine-queryable fields:
```yaml
---
title: ASSISTments 2009-2010 Skill Builder
type: dataset
source: CMU DataShop
url: https://pslcdatashop.web.cmu.edu/...
doi: 
license: CC-BY
date_added: 2026-04-27
last_verified: 2026-04-27
tags: [knowledge-tracing, math, K-12, student-performance]
---
```

**Markdown prose body** — dense description written for agent consumption:
what the resource is, what it's been used for, known limitations, key papers
that used it, relevant benchmarks, code that works with it.

This format is:
- Human-readable (maintainable)
- LLM-native (models are trained on markdown)
- Structured where it needs to be (frontmatter)
- Expressive where structure isn't enough (body)

---

## Karpathy's Architecture Applied to This Use Case

Karpathy's "compiler analogy" maps cleanly onto an educational resource wiki:

```
Source documents         →  CMU DataShop pages, AIMS resources,
(raw, heterogeneous)        grantee websites, papers, GitHub repos

Compilation              →  Weekly agent run: reads sources, extracts
(LLM processing)            structured metadata + prose description,
                            detects changes, flags gaps

Knowledge Store          →  /datasets/*.md, /frameworks/*.md,
(the wiki)                  /benchmarks/*.md, /code/*.md

index.md                 →  The agent reads this first. Flat list of
(navigation map)            everything with one-line descriptions.
                            No semantic search needed at this scale.

Query layer              →  Another agent reads index.md, decides
                            which files to fetch, synthesizes answer.
```

The key Karpathy insight: wiki entries are **deliberately authored** (by the
compilation agent), not mechanically sliced (like RAG chunks). The compilation
step is where intelligence lives — the query step becomes cheap.

---

## The index.md Specifically

At the scale of ~hundreds of resources, a flat index.md fits in a context window.
An agent can read the whole index, reason over it, and decide what to fetch next —
no vector search, no embeddings, no infrastructure.

What goes in index.md:
```markdown
# Educational Resources Index
Last updated: 2026-04-27

## Datasets
- [ASSISTments 2009-2010](datasets/assistments-2009.md) — Math tutoring logs,
  ~525k student responses, knowledge tracing baseline
- [PISA 2022](datasets/pisa-2022.md) — International student assessment,
  79 countries, reading/math/science
...

## Benchmarks
- [EduBench](benchmarks/edubench.md) — LLM evaluation on K-12 reasoning tasks
...

## Frameworks
- [Knowledge Component Model](frameworks/kc-model.md) — CMU/DataShop standard
  for skill tagging in tutoring data
...

## Code
- [pyBKT](code/pybkt.md) — Python implementation of Bayesian Knowledge Tracing
...
```

An agent scanning this index can answer "what datasets exist for knowledge
tracing in math" without any search infrastructure.

---

## The llms.txt Layer

`llms.txt` at the root is the *external* discovery mechanism — what an agent
sees when it arrives at the site cold. It points to index.md and explains the
structure. Think of it as the front door; index.md is the floor plan.

```markdown
# Educational Resources Wiki

> Agent-readable index of datasets, frameworks, benchmarks, and code samples
> for educational research. Updated weekly via automated scanning.

## Contents
- [Full index](index.md) — complete list of all resources
- [Datasets](datasets/) — learning interaction data, assessment data
- [Benchmarks](benchmarks/) — evaluation suites for AI in education
- [Frameworks](frameworks/) — conceptual and technical frameworks
- [Code](code/) — implementations, tools, libraries

## Sources scanned
CMU DataShop, AIMS, IES grantee sites, EDM conference proceedings
```

---

## What Makes This Different from an API

An API requires:
- Knowing the schema in advance
- Writing client code or queries
- Understanding authentication
- Handling pagination, rate limits

A markdown wiki with index.md requires:
- An HTTP GET
- The ability to read markdown (every LLM)
- No SDK, no client, no schema knowledge upfront

The wiki is self-describing in a way an API is not. An agent can figure out
what's here by reading the index — it doesn't need documentation to use the
documentation.

---

## Private Hosting Options

For a POC where content should be unlisted (not publicly indexed) but still
accessible to an LLM via WebFetch or equivalent:

| Option | Privacy | Persistence | Effort | Notes |
|---|---|---|---|---|
| ngrok tunnel | High — files stay local | Session-only | Low (have it already) | Kill tunnel = gone. Best for demo. |
| Secret GitHub Gist | Medium — unlisted, not indexed | Permanent | Low | Multiple files in one gist. Raw URLs fetchable. |
| HackMD secret | Medium | Permanent | Low | Markdown-native. Supports multi-file books. |
| MCP filesystem server | High — never leaves machine | Permanent | Very low | No tunnel needed. Claude Desktop reads local files directly. Better than ngrok for Claude specifically. |

**MCP filesystem server** (Anthropic's official MCP spec, November 2024) is worth
knowing about: it gives Claude Desktop direct `read_file` / `list_directory`
access to a local folder with zero tunneling. No public URL at all — the files
never leave the machine. For a POC with Claude specifically, this is cleaner than
ngrok. For a POC that any LLM/agent with WebFetch can use, ngrok is the right call.

## llms.txt vs llms-full.txt

Mintlify's CDN analysis across 25 companies found `llms-full.txt` received
3–4x more visits than `llms.txt`, with ChatGPT driving most of the traffic.
Interpretation: LLMs prefer loading complete documentation into context in one
request rather than navigating selectively via links.

**Implication for this design:** for a small index (74 AIMS resources), a single
`llms-full.txt` containing the complete index inline may outperform the
`llms.txt` → `index.md` → individual file navigation chain. Fewer fetches,
less latency, simpler architecture. Worth testing in the POC.

## Value-Add: Critical Assessment

The "agent-facing format" framing overstates the marginal difference between a
well-structured HTML page and a markdown file for modern LLMs. The real value is:

**Genuine gaps this fills:**
- Cross-source aggregation (AIMS + DataShop + IES grantees in one index)
- Consistent metadata schema across heterogeneous sources
- Programmatic stability (Squarespace redesigns; git repos don't)
- The Papers with Code gap for education (PWC shut down July 2025)

**Overstated:**
- "Agent-facing" as an architectural innovation — LLMs already read HTML fine
- "Eliminates discovery costs" — costs are real but not the bottleneck
- Update automation — mirrors existing sources' own maintenance burden

**MERLOT collaboration**: wrong target. MERLOT is curriculum OER; this is
research infrastructure (datasets, code, benchmarks). Non-overlapping missions.
Better collaboration target: AI-for-Education.org (same gap, already funded).

## The Hard Problems

**Incremental updates:** When a source changes, how do you reprocess only the
affected entries? Full regeneration weekly is probably fine at small scale;
becomes expensive as the index grows. The Karpathy compiler analogy applies —
this is the dependency tracking problem.

**Provenance and trust:** Automated scanning introduces errors. Each entry
needs a clear signal of what was human-verified vs. agent-generated, and when
it was last checked against the source.

**Scope creep:** Without a clear inclusion policy, the index becomes a list of
everything. The value is in curation — which means the compilation agent needs
explicit criteria for what qualifies.

**Freshness vs. stability:** Agents that build on this index need stable URLs.
If a dataset entry moves or is renamed, downstream agents break. This argues
for content-addressed or slug-stable URLs, not auto-generated paths.
