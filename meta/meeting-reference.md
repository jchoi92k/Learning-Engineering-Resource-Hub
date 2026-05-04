# Meeting Reference: Learning Engineering Resource Hub

---

## What Will actually built (policyhub.us — reviewed 2026-05-01)

Worth being precise here because Proposer referenced Will's hub as the model to emulate.
After a thorough review, Will's hub is **not LLM-facing**. It is a human-browsing site.

**What it is:**
- Built on Docusaurus (`/docs/` URL structure, static site generator)
- ~100 curated resources across readings, reports, CRS documents, toolkits
- State + federal bill tracking with weekly manually-updated tables
- DataWrapper charts for economic data visualizations
- Navigation: 6 main sections (State AI Bills, Federal AI Bills, Executive Actions, Datasets, Economic Trends, My AI Work)
- Resources organized by flat categories (General, Stats, Regulatory Frameworks, etc.) — no tagging system

**What it lacks (technically):**
- No `/llms.txt` (confirmed 404)
- No `/llms-full.txt` (confirmed 404)
- No structured data layer (no JSON, no API)
- Inconsistent metadata per entry: titles + URLs always present; dates and authors often missing; no type field
- No machine-readable structure — pure human-browsing HTML

**What Proposer admires about it:** the scope, the weekly cadence, the comprehensiveness of legislative tracking.
What Proposer may not realize: Will built a *human-facing* directory. The LLM-agent-facing part is Proposer's own addition to the idea.

**Implication:** We have already built something more technically sophisticated than Will's hub in the dimensions that matter for Proposer's vision (LLM-facing, structured metadata, tag system, JSON data layer). We just have narrower scope and no public hosting.

---

## What Proposer wants

Inspired by Will Rinehart's AI Policy Hub — a living, regularly-updated tracker but for AI in education.
Proposer's key addition to Will's model: **LLM-agent-facing as a core feature** (Will doesn't have this).

- Auto-updating index of papers, datasets, policy actions
- LLM-agent-facing is the key differentiator (not just a webpage)
- Broad scope: "AI and education" as a field

---

## What Stakeholder wants

Narrower and more concrete than Proposer's vision:

- Focus specifically on **learning engineering** as a field
- Tie it to an existing TLA product page (tools competition, renphil — TBD)
- An "agent around learning engineering" — still unclear if that means a queryable index or something more interactive

---

## What we built

A working proof-of-concept of the LLM-facing format Proposer described.

- **89 resources** indexed with metadata (title, type, tags, description, URL)
- **Sources:** AIMS Collaboratory (79), The Learning Agency (2), CMU LearnLab + Simon Initiative + DataShop (3), ASSISTments (1), CoSN (3), learningengineering.org (1)
- **Navigation:** browse by domain (getting started / LE practice / research / datasets / policy) or by tag (47 tags across affiliation, method, topic, domain)
- **Format:** plain text flat files — one fetch loads the full index; designed for LLM consumption
- **Tested:** live query via Claude web UI returned accurate synthesized answers with correct stats

**What it is not yet:**
- Not auto-updating (no pipeline)
- Not publicly hosted (running locally via ngrok for demo)
- Not covering legislation or broad "AI in education" policy

---

## How it maps to their visions

| | Proposer | Stakeholder | What we have |
|---|---|---|---|
| Domain | AI + education broadly | Learning engineering specifically | LE-focused, expandable |
| Auto-update | Yes (weekly like Will's) | TBD | No — described, not built |
| LLM-facing | Core selling point | "Agent around LE" | Yes — confirmed working |
| Hosted | Public site | TLA product page | Local + ngrok (demo only) |
| Policy tracking | Yes | TBD | Minimal (CoSN guidance only) |
| Datasets | Yes | TBD | 1 entry (DataShop) |

---

## The honest gaps

1. **Auto-update** is Will's killer feature — we don't have it yet. The path exists (OpenAlex API for papers, Legiscan for policy) but needs build.
2. **Scope** is still narrow. Proposer's vision is much broader than what we indexed.
3. **"Agent" vs. "index"** — worth clarifying with Stakeholder. A queryable index (what we built) is very different from a task-completion agent (e.g., "help me design an experiment"). The ChatGPT for Education article Stakeholder forwarded describes the latter.

---

## What to offer

- Share the POC + demo query as evidence the format works
- Offer to flesh it out further if there's appetite
- Flag the key design decisions that need alignment before scaling: who maintains it, what's in scope, where it lives

---

## On the Karpathy LLM Wiki pattern (flag for meeting)

In April 2026, Andrej Karpathy posted a GitHub gist describing a different but related idea that went massively viral (16M+ views, 5,000+ stars). Worth flagging because Proposer may have seen it — but it's not what he meant.

**What Karpathy describes:** A persistent wiki where an LLM *writes and maintains* the content. You feed it source documents; it synthesizes them into structured pages. The output is an opinionated knowledge base — "here's what the field says about spacing effects" — not a directory of links.

**What Proposer meant:** A directory in the style of Will's hub — a regularly-updated index of resources, papers, and policy actions. Closer to a card catalog than an encyclopedia.

These are two different products:

| | Karpathy wiki | What Proposer described |
|---|---|---|
| Output | LLM-synthesized content pages | Links + metadata |
| LLM role | Author (writes the wiki) | Reader (queries the index) |
| Source material | Documents you ingest | External URLs you point to |
| Analogy | Encyclopedia | Card catalog |
| Closest real example | Personal research knowledge base | policyhub.us (but LLM-facing) |

If Proposer has seen the Karpathy buzz and now wants *that* — that's a bigger, different project. Worth a quick check in the meeting. Our POC is the card-catalog model; the Karpathy model would require ingesting and synthesizing the actual source documents, which raises scope, accuracy, and maintenance questions we haven't addressed.

Both are valid long-term directions. They're not mutually exclusive — you could have a referratory layer *and* a synthesis layer. But they shouldn't be conflated.

---

## Landscape context (added 2026-05-01)

The format we chose has a name: the **llms.txt standard** (Jeremy Howard / Answer.AI, Sept 2024). Our `llms.txt` + `llms-full.txt` structure matches this spec. Major adopters: Anthropic, Cloudflare, Vercel, Stripe, Cursor.

**AI Policy Hub (policyhub.us) is NOT LLM-facing.** It's a human-browsing site with no `/llms.txt` or agent endpoints. We were inspired by its scope and update cadence, not its format.

**Karpathy LLM Wiki pattern** (April 2026, 16M+ views) describes the complementary idea: a persistent, LLM-maintained internal wiki. Their `index.md` + `log.md` + `CLAUDE.md` pattern is what we'd add to make our hub agent-*maintained*, not just agent-*readable*. The two patterns are compatible.

**Context7** (Upstash) is the MCP-server model: wrap the knowledge base as callable tools (`wiki_search`, `wiki_get`). This is the highest-integration approach but requires the agent's environment to have the MCP server installed. Out of scope for now.

See `docs/llm-wiki-landscape.md` for the full analysis.
