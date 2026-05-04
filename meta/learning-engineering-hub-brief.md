# A Living Resource Hub for Learning Engineering
## What Proposer means, what it would take, and where we are

---

## The Inspiration: What Will Rinehart Built

Will Rinehart recently launched **AI Policy Hub** (policyhub.us), a website that tracks AI-related legislation, government actions, and economic trends — and updates itself automatically every week.

Here is what makes it useful:

- **It stays current.** Every Monday, a script runs automatically, pulls the latest state and federal AI bills, and rebuilds the site. You don't have to manually check anything.
- **It covers multiple angles.** Bills from all 50 states. Federal legislation. Executive orders. Economic data. Research papers. All in one place.
- **It's built to be queried.** Will is explicitly planning to feed the data into an AI for analysis — the site is structured so that is easy to do.

It is essentially a living dashboard for anyone who needs to track what's happening in AI policy.

---

## What Proposer Is Asking For

Proposer's idea, in his words: *"Imagine this but for AI and education — a running wiki that just updates on papers, datasets, policy actions, etc."*

He is asking for the same thing Will built, but pointed at the education space instead of policy. Specifically:

| What Will tracks | Education equivalent |
|---|---|
| State & federal AI bills | State & federal legislation on AI in education, student data privacy, ed-tech |
| Government/agency actions | Dept. of Education guidance, FERPA updates, AI-in-education policy memos |
| Economic research papers | Research papers on AI's effects on learning outcomes |
| Empirical data charts | Student performance trends, ed-tech adoption rates |

The key phrase from Proposer is **"running wiki"** — meaning it updates on its own, not a document someone maintains by hand. The LLM-agent-facing format (being queryable by AI) is what Proposer sees as the differentiating feature compared to a normal website.

---

## What Stakeholder Is Scoping It To

Stakeholder's framing is narrower and more actionable: **learning engineering** specifically.

Learning engineering is the professional practice of using evidence, data, and experimentation to improve how people learn — think: A/B testing in curricula, measuring what instructional approaches actually work, using AI to analyze student strategies at scale. It's a defined field with its own community, conferences, and body of research.

Focusing on learning engineering means the hub would be most useful to:
- Researchers and practitioners in the field
- Organizations like TLA that produce and consume this kind of evidence
- Ed-tech developers who want to understand what's been studied

Stakeholder is also asking where this lives — *"maybe on tools competition page? or renphil?"* — which means the output would be tied to an existing TLA product or page, not a standalone site.

---

## What We've Already Built

A working proof-of-concept that demonstrates the format and pipeline for this kind of hub. Specifically:

- **79 resources** from the AIMS Collaboratory, indexed with metadata: title, type, source, tags, description, URL
- **Structured for AI querying** — all entries live in a single flat file that an AI agent can fetch and search in one request
- **Tested**: ran a live query against it and got back accurate, synthesized answers with correct statistics

What it covers overlaps heavily with learning engineering: A/B testing platforms (UpGrade), AI analysis of student math strategies (ASTRA, Carnegie Learning), automated instructional quality analysis, coaching tools, student motivation measures.

**What it isn't yet:**
- It covers only one source (AIMS Collaboratory)
- It was built as a snapshot, not auto-updating
- It is running locally, not hosted publicly

---

## What a Minimal Version Would Require

To go from POC to a real hub for learning engineering, there are three layers:

### Layer 1: Content (what goes in it)
Sources to pull from, beyond AIMS:
- **The Learning Agency** research and guides
- **IES / What Works Clearinghouse** — the federal clearinghouse for ed research
- **Carnegie Mellon / DataShop** — the largest repository of learning data and research
- **EDM / LAK conference proceedings** — the two main learning analytics/data mining conferences
- **learningengineering.org** — the field's home base

This is the editorial question: who decides what's in scope?

### Layer 2: Pipeline (how it stays current)
Will's approach, adapted for education:
- **Papers**: OpenAlex (a free academic database with an API, covers most journals and conferences) — query weekly for "learning engineering" keywords, flag new entries automatically
- **Policy**: Same Legiscan API Will uses, but with education-specific keywords (AI + education, student data, ed-tech, etc.)
- **Tools and platforms**: No API exists for these — requires manual curation

The automation part is the important difference between a living hub and a snapshot.

### Layer 3: Hosting and access
Will uses Hugo (a free static site generator) + GitHub, which rebuilds the site automatically when new data comes in. A simpler option for a first version: GitHub Pages with a weekly script. Either way, this is cheap or free to host.

---

## Effort Estimate

| Version | What it includes | Effort |
|---|---|---|
| Expand the POC | Add 30-50 resources from LE sources; reframe as learning engineering; host publicly | 2–3 days |
| Add auto-update for papers | Connect OpenAlex API + weekly GitHub Action for new papers | 1–2 weeks |
| Full hub (Will-equivalent) | Papers + policy tracking + datasets + hosted dashboard | 2–3 months ongoing |

The minimal useful version — something Stakeholder could show Proposer and that would actually be queryable — is the first row. The key open question is whether it's hosted publicly (anyone can use it) or internal to TLA.

---

## The One Thing to Clarify With Proposer and Stakeholder

The ChatGPT-style "agent" (a bot that answers questions, books appointments, drafts emails) is a different thing from what Proposer described. What Proposer wants is closer to **a structured, auto-updating index** — a knowledge resource, not a task-completion tool. The distinction matters for scoping the project. A knowledge index is much more tractable as a first step.

---

*Draft prepared 2026-05-01. Based on review of Will Rinehart's AI Policy Hub write-up (Exformation, Apr 29 2026) and internal project context.*
