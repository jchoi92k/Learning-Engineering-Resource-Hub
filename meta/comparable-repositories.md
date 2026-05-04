# Agent-Facing Wiki: Concept, Comparables, and Gap Analysis

---

## The Idea (as proposed)

- Wiki structure rather than traditional resource library
- Optimized for agent consumption, not human browsing
- Automated scanning of CMU DataShop, AIMS, grantee websites
- Weekly updates linking to datasets, frameworks, benchmarks, code samples
- Eliminates UX/UI complexity and discovery costs

---

## Comparable Systems

### Papers with Code [DEFUNCT as of July 2025]
- **What it was:** Wikipedia of ML research — papers linked to implementations,
  benchmarks organized as (Task, Dataset, Metric) tuples, leaderboards showing
  top scores with code. The closest functional analog to this idea for ML broadly.
- **Scale at shutdown:** 9,327 benchmark leaderboards, 79,817 paper-code links,
  5,628 datasets
- **Shutdown:** Meta closed it July 24–25, 2025 without prior notice, despite a
  public commitment at acquisition (December 2019) to keep it "neutral, open and free."
  Domain now redirects to Hugging Face Trending Papers.
- **Data preserved:** JSON dumps on GitHub; `pwc-archive` on Hugging Face; 2021-era
  import into Open Research Knowledge Graph
- **Gap:** No successor replicates the unified paper-code-benchmark-dataset linkage.
- **Source:** https://www.codesota.com/papers-with-code

### AI-for-Education.org — Benchmark Finder
- **URL:** https://ai-for-education.org/find-benchmarks/
- **What it is:** Education-specific benchmark index built on Papers with Code data.
  ~10,000 datasets, ~160,000 papers. Semantic search interface.
- **Maintained by:** Fab Inc. + Team4Tech, funded by Bill & Melinda Gates Foundation
  and Jacobs Foundation
- **Gap:** Human-facing (no confirmed public API), narrow scope (AI benchmarks only,
  not broader educational resources), not auto-updating, acknowledges gaps in pedagogy
  and content alignment benchmarks
- **Verification:** Fetched directly — content confirmed

### LearnSphere / CMU DataShop
- **URLs:** https://learnsphere.org/ | https://pslcdatashop.web.cmu.edu/
- **What it is:** "World's largest learning analytics infrastructure." Combines:
  - DataShop (CMU) — 705,000+ hours of student data, 1,466 datasets, 358,000 students
  - MOOCdb (MIT)
  - DataStage (Stanford)
  - DiscourseDB (discussion/collaborative learning data)
- **API:** DataShop has a web services API for dataset identification and export at
  transaction/student-step level. LearnSphere as a whole: no explicit public API confirmed.
- **Maintenance:** CMU + MIT + Stanford + University of Memphis, NSF-funded
- **Gap:** Database infrastructure for researchers, not agent-facing; gated access;
  no discovery layer; Tigris workflow tool is internal, not public-facing
- **Verification:** Fetched directly — content confirmed

### Karpathy's LLM Knowledge Base (architecture proposal, not a deployed system)
- **Sources:**
  - https://www.mindstudio.ai/blog/karpathy-llm-knowledge-base-architecture-compiler-analogy
  - https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an
- **What it is:** A proposed personal knowledge base architecture optimized for LLM
  consumption rather than human browsing. Four layers:
  1. **Source** — raw documents (PDFs, web pages, notes)
  2. **Compilation** — LLM processes source into structured artifacts (fact extraction,
     entity mapping, multi-level summaries, Q&A pairs, gap flagging)
  3. **Knowledge Store** — wiki with linked entries; entries are "deliberately authored
     by the LLM rather than mechanically sliced" (contrast with RAG chunks)
  4. **Query** — agents query pre-structured knowledge; model synthesizes, doesn't
     interpret raw prose
- **Key difference from RAG:** Moves intelligence earlier in the pipeline. RAG retrieves
  raw chunks at query time. This approach processes everything upfront into structured
  wiki entries, yielding higher retrieval precision and lower hallucination risk.
- **index.md:** A navigation map the agent reads first to understand what exists and
  where — replaces semantic search for navigation at personal KB scale (~100 articles,
  ~400k words fits in a context window).
- **Hard problem:** Incremental compilation — when source documents update, how to
  reprocess only affected artifacts without full regeneration.
- **Status:** Conceptual proposal / personal system. Not institutionally deployed.

### llms.txt Standard
- **Spec:** https://llmstxt.org/
- **Proposed by:** Jeremy Howard (Answer.AI), September 3, 2024
- **What it is:** A convention for exposing LLM-friendly content at `/llms.txt` on any
  website. Markdown format: H1 project name, blockquote summary, links to detailed
  markdown files. Analogous to robots.txt but for LLM agents instead of search crawlers.
- **Adoption:** 844,000+ sites as of October 2025 (BuiltWith tracking). Anthropic,
  Cursor, and Mintlify-hosted docs sites among early adopters.
- **Caveat:** Despite adoption, actual LLM crawler traffic to llms.txt files was
  negligible through late 2025 (zero visits from Google-Extended, GPTbot,
  PerplexityBot, ClaudeBot per tracked data mid-August to late October 2025).
- **Role in this idea:** Discovery layer — not a content format but a way for agents
  crawling in from the outside to find what the wiki contains.

### Topham et al. 2025 — AI in Educational Technology: Systematic Review of Datasets
- **DOI:** 10.1145/3768312
- **Journal:** *ACM Computing Surveys*, Vol. 58, pp. 1–28, 2025
- **Authors:** Luke K. Topham, Pete Atherton, Tom Reynolds, Yasir Hussain, A. Hussain,
  Hoshang Kolivand, Wasiq Khan
- **Abstract [VERIFIED via Semantic Scholar]:**
  > Surveys AI applications in secondary and higher education including predicting
  > performance, curating learning materials, and automated assessment and feedback.
  > Identifies gaps: limited attention to traditional classrooms and non-scientific
  > subjects. Compiles available datasets. Highlights that "many AI in Education (AIEd)
  > platforms are not grounded in educational theory."
- **OA status:** Not confirmed. No PDF URL in Semantic Scholar.
- **Relevance:** Closest thing to a systematic map of educational AI datasets as of
  2025 — but a static review article, not a live index.

---

## Gap Analysis

No system currently combines:
- [ ] Agent-facing format (not human-UX)
- [ ] Education-specific scope (datasets, frameworks, benchmarks, code)
- [ ] Automated scanning / weekly updates
- [ ] Open, unauthenticated access
- [ ] Unified linking across resource types (paper ↔ dataset ↔ code ↔ benchmark)

Papers with Code had all of these for ML generally and is now gone.
LearnSphere has the data but not the format or access model.
AI-for-Education.org has the scope but not the format, automation, or API.
Karpathy's proposal has the architecture but is personal-scale and undeployed.

---

## Design Notes (see separate file)

See `agent_facing_wiki_design.md` for what "agent-facing" means technically
and what format choices the architecture implies.
