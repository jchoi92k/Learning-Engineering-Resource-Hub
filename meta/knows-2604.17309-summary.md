# Summary: Knows — Agent-Native Structured Research Representations

**arxiv:** 2604.17309  
**Authors:** Guangsheng Yu, Xu Wang  
**Submitted:** April 19, 2026  
**Fetched and summarized:** 2026-05-03 (from arxiv.org/html/2604.17309)

---

## What it is

Knows introduces **KnowsRecord** — a lightweight YAML "sidecar" that accompanies a research PDF. The sidecar encodes structured claims, evidence, provenance, and typed relations in a form LLM agents can consume without parsing the full document. The original PDF is unchanged; the sidecar is an additional file.

A community hub at knows.academy/ has indexed 10,000+ publications.

---

## Core specification (v0.9)

30 root-level fields, 23 entity definitions. Five primary entity collections:

1. **Artifacts** — declare the paper and cited works with typed identifiers
2. **Statements** — claims, assumptions, limitations, methods, questions, definitions; each tagged with modality (empirical/theoretical/descriptive/normative) and two-dimensional confidence scores
3. **Evidence** — observations linked to statements, with numeric values or qualitative descriptions
4. **Relations** — typed directed graph: `supported_by`, `challenged_by`, `depends_on`, `limited_by`, `uses`, `evaluates_on`, `implements`, `documents`, `cites`, `same_as`, `supersedes`, `retracts`
5. **Actions** — optional executable hooks with safety policies

---

## Evaluation design

- 140 comprehension questions across 20 classic papers, 14 disciplines
- 6 LLM agents across 3 tiers: weak (Qwen3.5-0.8B, Qwen3.5-2B), medium (MiMO-V2-Flash, Qwen3.5-27B), strong (MiMO-V2-Pro, Kimi-K2.5)
- 3 conditions: PDF-only, Knows-only, Knows+Fallback

---

## Key results

### Accuracy (E1)

| Model | PDF accuracy | Knows accuracy | Delta |
|---|---|---|---|
| Qwen3.5-0.8B (weak) | 19% | 47% | +28 pp |
| Qwen3.5-2B (weak) | 25% | 67% | +42 pp |
| Medium/strong | Varies by discipline | Inconsistent | — |

Gains scale with paper length. On LONG papers (>20K words), Qwen-0.8B improves from 7% to 64% (+57 pp).

With LLM-as-judge scoring (Claude Sonnet 4), weak-model sidecar accuracy (75–77%) **approaches** stronger-model PDF accuracy (78–83%) — meaning cheap models + sidecars roughly match expensive models reading full PDFs.

Medium and strong models show **discipline-dependent patterns**, not consistent improvement. The accuracy gain story is primarily about weak models.

### Token efficiency (E2/E3)

- 29–86% fewer input tokens vs. PDF
- Low end (29%): weak models whose tokenizers truncate long PDFs anyway
- High end (86%): MiMO-V2-Pro (2,856K → 401K tokens)
- Latency: 3.4–4.6× speedup for locally-run weak models; marginal for API-served models (network overhead dominates)

### Ablation: statements-only variant (E8)

Full sidecar matches PDF accuracy (59%) with 55% fewer tokens.  
**Statements-only** retains 88% of full-sidecar accuracy while consuming **93% fewer tokens** than PDF = **12.7× token efficiency**.  
Dropping relations costs 1 pp accuracy; dropping evidence costs 2 pp.

### Statement granularity (E9)

The uniform ~7-statement template used in E1–E8 **underestimates optimal granularity**. Dense sidecars (15–25 statements) improve medium and strong models by +13 to +60 pp on complex papers. The Gödel paper reaches 100% accuracy across all four model tiers with dense representation.

Implication: the evaluation likely understates potential gains from well-authored sidecars.

### Review traceability (E4)

Per-weakness ID references: 0% from PDF-based reviews vs. 64–91% from Knows-based reviews. Note: prompt asymmetry partially accounts for this (Knows condition explicitly prompted for IDs).

### Structural vs. semantic validation (E5)

- Structural corruption (missing fields, broken references): 100% detection by `knows-lint`
- Semantic corruption (wrong numbers, inflated confidence): **0% detection**

Structural validation is solved; semantic validation is not. A real DP-SGD epsilon-accuracy inversion was discovered during evaluation and not caught automatically.

---

## Limitations (from the paper itself)

1. **Circular evaluation bias** — Both the sidecars AND the benchmark questions were authored by Claude Opus. The model that generated the structured data is related to the model used for scoring. This is a real validity concern.
2. **Uniform granularity** — E1–E8 used a fixed ~7-statement template. E9 shows this understates optimal performance by up to 57 pp. The headline accuracy numbers are lower-bound estimates.
3. **Paper selection bias** — All 20 papers are well-known classics. Modern papers with supplementary materials, datasets, and code are untested.
4. **Model coverage** — 6 models tested (5 excluded for insufficient coverage); Llama, Gemini, GPT architectures not tested.
5. **English only.**
6. **Generation constraints** — E7 uses only first 15K characters per paper due to API limits.

---

## Relevance to our hub

### What transfers

- **YAML metadata per entry outperforms unstructured text** for agent consumption — this is the core validated claim, and our hub's YAML frontmatter is an instance of this pattern.
- **The sidecar concept** (structured metadata alongside, not replacing, the source) is exactly what we do: we provide metadata + URL, not hosted content.
- **Token efficiency is real** — agents loading our YAML entries consume fewer tokens than agents reading the raw source pages.
- **The "statements-only" finding** has a direct analog for our dual-track architecture idea: a lean shard (title, url, type, source, tags — no description) retains most navigational utility at much lower token cost.

### What doesn't transfer directly

- Knows is designed for **research paper comprehension** (Q&A over specific papers). Our hub is a **discovery index** (find and filter resources by domain/type/tag). The task structure is different.
- Our YAML fields (url, type, source, tags, description) are much simpler than KnowsRecord's 30-field schema. We don't encode claims, evidence chains, or typed relations between entries.
- The accuracy gains are largest for weak models reading complex papers. Our use case is typically a capable model doing a broad search — less directly analogous.
- Circular bias in the evaluation means the numbers (especially the LLM-as-judge scores) should be read with some skepticism.

### The relevant insight

The paper validates the category our hub belongs to. It doesn't validate our specific implementation, but it establishes that "structured YAML metadata per research entry, consumed by agents" is a sound, empirically-grounded approach — not an ad-hoc choice.

---

## Dual-track architecture implication

The statements-only ablation (E8: 93% fewer tokens, 88% of accuracy) directly supports a dual-track design:

- **Full track** (`llms-full.txt` or per-source shard): title + YAML frontmatter + full description. For agents doing deep exploration or needing the description to assess fit.
- **Lean track** (per-category index): title + url + type + source + tags only, no description. For agents that know what category they want and need to scan many entries cheaply.

The Knows finding suggests the lean track will retain most navigational utility — the tags and type fields carry most of the signal for discovery tasks.

---

*Source: arxiv.org/html/2604.17309. Fetched 2026-05-03. All numbers verified against HTML full text.*
