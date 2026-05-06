# RAG Optimization Research — Applied to Our Knowledge Base

> Researched 2026-05-06. Covers 2025–2026 findings from Google, Anthropic, OpenAI, and academic sources.
> Context: 569-entry knowledge base (557KB data.json), delivered via Gemini Gem with RAG retrieval.

---

## What the major providers say

### Anthropic — Contextual Retrieval (September 2024, still current)

The most actionable RAG research for our use case. Key finding: prepending a 50–100 token "situating context" to each chunk before embedding reduces retrieval failures by 49% (67% with reranking added).

**How it works:** Before embedding a chunk, an LLM generates a brief context prefix explaining where this chunk fits in the larger document. A raw chunk like `"Five recommendations for grades 4–8..."` becomes `"This is entry 3 from a What Works Clearinghouse practice guide on math problem solving. Five recommendations for grades 4–8..."` The prefix gives the embedding model enough signal to match queries that use different terminology.

**Benchmark numbers:**
- Baseline RAG: 87.15% recall @ top 10
- + Contextual embeddings: 92.34% (+5.2 points)
- + Reranking: 95.26% (+8.1 points total)

**Applicability to us:** We don't control Gemini's embedding pipeline, so we can't add contextual embeddings directly. But we CAN bake the same idea into the file format — make each entry self-contextualizing by including type, source, and tags as natural language in the same text block as the description. This is the "poor man's contextual retrieval."

Source: https://www.anthropic.com/news/contextual-retrieval
Source: https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide

---

### OpenAI — File Search internals

OpenAI's file search uses **800-token chunks with 400-token overlap** by default (customizable 100–4096 tokens). Hybrid keyword + semantic search with text-embedding-3-large. Retrieves up to 20 chunks within a 16,000-token budget.

**Applicability to us:** OpenAI's 800/400 chunking means a JSON entry that spans ~150 tokens would be grouped with 4–5 neighboring entries in a single chunk. If the user asks about "math tutoring RCT," the chunk might contain a math entry AND an unrelated literacy entry, diluting relevance. Self-contained entries separated by clear delimiters would give the chunker natural break points.

Source: https://developers.openai.com/api/docs/assistants/tools/file-search

---

### Google — Vertex AI RAG Engine

Google's Vertex AI RAG Engine supports JSON, Markdown, TXT, and other formats. Google publishes surprisingly little prescriptive guidance on chunk sizes or formatting — their docs point to a "fine-tune RAG transformations" page without concrete numbers.

**For Gemini Gems specifically:** No public documentation on how Gems chunk or index uploaded files. Community reports suggest Gems sometimes ignore attached files when instructions are long, and recommend adding "Always reference the attached files before answering" prominently in instructions.

**Applicability to us:** Since Google doesn't publish Gems' internal chunking, we can't optimize for their specific pipeline. But the general principles apply: self-contained chunks, clear delimiters, metadata inline.

Source: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/supported-documents
Source: https://support.google.com/gemini/answer/15235603

---

## Key research findings (2025–2026)

### Document format: Markdown outperforms

SearchCans 2026 benchmark across 100 web pages:

| Format | Avg Tokens | Retrieval Accuracy |
|---|---|---|
| Raw HTML | 38,400 | 62% |
| Plain Text | 1,850 | 71% |
| Semantic Markdown | 2,100 | **89%** |

Markdown preserves structural cues (headings, bold, lists) while eliminating noise. Additional sources confirm clean Markdown improves retrieval accuracy by up to 35% vs unstructured text.

**Applicability to us:** Our data.json is structured JSON, not markdown. JSON keys (`"num"`, `"tags"`, `"url_confirmed"`) are structural noise for an embedder. A Markdown version where each entry uses headings and inline formatting would give the embedder better semantic signals.

Source: https://www.searchcans.com/blog/markdown-vs-html-rag-benchmark/
Source: https://anythingmd.com/blog/why-llms-need-clean-markdown

---

### Chunk size: 256–512 tokens optimal, semantic chunking overrated

NVIDIA research: factoid queries perform best at 256–512 tokens; multi-hop queries benefit from 512–1024.

**Vectara study (NAACL 2025):** Fixed-size chunking consistently outperformed semantic chunking across document retrieval, evidence retrieval, and answer generation. Chunking configuration influences retrieval quality as much as or more than embedding model selection.

**Applicability to us:** Our average entry is ~100–180 tokens. At 256–512 token chunks, Gemini likely groups 2–4 entries per chunk. Entries that naturally belong together (e.g., three WWC math guides in sequence) benefit; entries that don't (a math guide next to a reading guide) get noise. Adding clear delimiters (e.g., `---` between entries) gives the chunker obvious break points.

Source: https://weaviate.io/blog/chunking-strategies-for-rag (references NVIDIA and Vectara findings)

---

### Metadata: structured fields beat inline-only

Consensus from Vectorize, Unstructured, deepset: store metadata as structured key-value pairs alongside embeddings for pre-retrieval filtering. Tags as structured fields enable `filter by tag = "math-education"` BEFORE semantic search runs.

**Applicability to us:** We don't control Gemini's vector store, so we can't add metadata filters. But we CAN include metadata as natural language in each entry's text so it gets embedded alongside the description. The entry text should read like `"Tags: math-education, k-12, math-strategies"` not `"tags": ["math-education", "k-12", "math-strategies"]` — the former is embeddable, the latter is syntax.

Source: https://docs.vectorize.io/build-deploy/data-pipelines/understanding-metadata/
Source: https://unstructured.io/insights/how-to-use-metadata-in-rag-for-better-contextual-results
Source: https://www.deepset.ai/blog/leveraging-metadata-in-rag-customization

---

### Small corpus: RAG still beats context-stuffing when <20% is relevant per query

For a 569-entry knowledge base where a typical query matches 5–20 entries (~1–4% of corpus), RAG is the right approach. Full-context stuffing suffers from "lost in the middle" — multi-fact retrieval recall drops to ~60% when information is buried mid-context.

**Applicability to us:** Confirms that Gemini Gems' RAG approach (retrieve relevant chunks, not load the whole file) is correct for our scale. But it means retrieval quality IS the bottleneck — a missed entry in retrieval is a missed entry in the response.

Source: https://tianpan.co/blog/2026-04-09-long-context-vs-rag-production-decision-framework
Source: https://ragflow.io/blog/rag-review-2025-from-rag-to-context

---

## What we can actually do (given we don't control Gemini's RAG pipeline)

We have exactly one lever: **the format and content of the uploaded file.** Everything else (embedding model, chunk size, retrieval algorithm, reranking) is Gemini's black box.

### Recommended changes

**1. Generate a Markdown knowledge file optimized for RAG chunking.**

Transform data.json entries from:
```json
{"num": 3, "title": "Improving Mathematical Problem Solving...", "type": "framework", "source": "What Works Clearinghouse", "tags": ["math-education", "k-12", ...], "desc": "Five recommendations..."}
```

To:
```markdown
---

### 3. Improving Mathematical Problem Solving in Grades 4 Through 8

Type: framework | Source: What Works Clearinghouse
Tags: math-education, k-12, math-word-problems, math-strategies, learning-engineering
URL: https://ies.ed.gov/ncee/wwc/PracticeGuide/16

Prepared by Mathematica. Five recommendations for teachers, math coaches, and curriculum developers targeting grades 4–8: preparing problems for whole-class instruction, supporting student self-monitoring and reflection, teaching visual representation, exposing students to multiple solution strategies, and helping students recognize mathematical concepts and notation.
```

**Why this helps (mapped to research):**
- Markdown format: +18 percentage points retrieval accuracy over plain text (SearchCans benchmark)
- Self-contained entries: approximates Anthropic's contextual retrieval (type + source + tags as natural-language context prefix)
- `---` delimiters: gives the chunker natural break points (Vectara finding: chunking config matters as much as embedding model)
- Tags as inline text: embeddable by the vector model, not hidden behind JSON syntax (metadata research consensus)
- Heading per entry (`### 3.`): Markdown structural cue that embedders can use for section detection

**2. Add a preamble that reinforces the tag taxonomy.**

First ~500 tokens of the file should list all 66 tags grouped by category. This gets embedded as its own chunk and helps the model translate user queries into tag vocabulary — e.g., "struggling math students" → `math-education, response-to-intervention, math-strategies`.

**3. Keep data.json as-is for the web UI and API consumers.** The Markdown file is a generated export for Gem upload only. Added to `build_tags.py` as another output alongside llms-full.txt and tag files.

---

## What NOT to do

- **Don't try to control Gemini's chunk size.** We can't.
- **Don't add redundant "search keywords" to entries.** The description and tags already contain the relevant terms. Keyword stuffing degrades embedding quality.
- **Don't split into multiple small files.** Gemini allows 10 files, but splitting the corpus means retrieval must search across files — no evidence this helps, and it complicates updates.
- **Don't switch to CSV.** Some sources suggest CSV for structured data, but CSV loses the Markdown structural cues that improve retrieval accuracy.
