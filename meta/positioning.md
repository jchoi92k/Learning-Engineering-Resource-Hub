# Renaissance AI and Education Resource Hub — Positioning

## What It Is

The Renaissance AI and Education Resource Hub is a structured, curated index of evidence-based K-12 and higher education resources — built to be readable by both humans and AI agents.

It currently holds 569 entries spanning research papers, practice guides, datasets, frameworks, and tools from organizations including the What Works Clearinghouse, CASEL, the Campbell Collaboration, JEDM, JLA, Digital Promise, the Learning Policy Institute, EdTrust, IES REL, and others.

## Why It Exists

Resource libraries have always been built for humans to browse. That model is changing.

AI agents — in coding environments, chat interfaces, and automated pipelines — are increasingly capable of searching, fetching, and reasoning over structured knowledge. But most existing education resource libraries are not structured for this. They are web interfaces, PDFs, and search engines designed for human navigation.

The Renaissance Hub is built on the premise that the same curated knowledge that helps a practitioner should also be directly accessible to an AI agent acting on their behalf. This is what we call a **resource library for agents**: a knowledge asset structured for machine consumption without sacrificing human readability.

## How It Works

The hub delivers the same corpus through three channels depending on the use case:

| Channel | Best for | Access |
|---|---|---|
| **MCP server** | AI coding agents (Claude Code, Cursor, Copilot, Windsurf) | Add URL to MCP config |
| **Gemini Gem** | Chat-based AI assistants | Custom Gem with bundled knowledge file |
| **Web app** | Human browsing, discovery, sharing | GitHub Pages |

All three channels draw from the same underlying data — `data.json`, generated from the curated entry list by `build_tags.py`.

## Editorial Standards

Every entry in the hub comes from an organization that applies a named, external evidence standard:

- **What Works Clearinghouse** — IES Standards Handbook (randomized controlled trials, quasi-experimental designs)
- **Evidence for ESSA** — ESSA Section 8101(21)(A) evidence tiers (Strong, Moderate, Promising)
- **Campbell Collaboration** — PRISMA systematic review protocol
- **JEDM / JLA** — Peer-reviewed journals with named editorial boards
- **National Academies Press** — National Academies consensus process
- **CASEL** — Established SEL framework with documented review criteria

An organization merely claiming "we review our content" is not sufficient for inclusion. The standard must be named and externally recognized.

## What It Is Not

- It is not a search engine for the open web.
- It does not host or reproduce any content — links only.
- It is not a task-completion agent. It is a knowledge index.
- It does not auto-update. Curation is manual and deliberate.

## Current State (POC)

The hub is a proof of concept. Strengths at this stage:

- 569 entries across major evidence-based education organizations
- MCP server live and validated
- Three delivery channels functional
- Editorial standards documented and applied

Known gaps:

- Coverage is uneven — some high-value sources (WWC intervention reports, Evidence for ESSA Moderate tier) are only partially indexed
- No contribution channel yet — submissions must go through the maintainer
- No auto-update — new publications require manual indexing runs

## The Longer-Term Vision

At scale, the hub becomes a standing knowledge infrastructure for the learning engineering and AI-in-education community: a place where new research gets indexed as it's published, where practitioners can find the evidence base for their tools, and where AI agents can pull from a vetted corpus rather than the open web.

The auto-updating dimension — where new publications are discovered, fetched, and indexed on a schedule — is a separate project that builds on this foundation. The POC demonstrates that the architecture is sound.
