# Inclusion Criteria — Learning Engineering Resource Hub

> Derived from a survey of comparable education repositories and clearinghouses.
> See `docs/comparable-repositories.md` for the underlying research.

---

## Summary statement

This hub is a **referratory**: links + metadata, agent-readable, no content hosting. It does not rate individual studies. It trusts the editorial judgment of pre-curated source organizations and indexes what they have surfaced. Inclusion decisions happen at two levels: (1) whether a *source* belongs in the hub, and (2) whether a specific *resource* from that source belongs.

---

## Level 1 — Source inclusion criteria

A source organization qualifies for systematic indexing if it meets **all three**:

1. **Editorial accountability**: The organization has a documented review or selection process — peer review, expert panel, evidence standards, or equivalent editorial board. Self-published vendor content does not qualify.
2. **Public access**: Resources are freely accessible (HTML, open-access PDF, or equivalent). Paywalled content is excluded unless an open-access version exists via Unpaywall or institutional repository.
3. **Relevance to evidence-based education**: The source publishes research findings, evidence syntheses, frameworks, or tools directly relevant to K-12 or higher education learning outcomes, instruction, or learning systems design.

### Positive signals (any one strengthens the case)
- Federal or major foundation funding (IES, NSF, Gates, Hewlett, Carnegie)
- Peer-reviewed publication or editorial board review
- Systematic review methodology (PRISMA, Campbell standards, or equivalent)
- Adopted as a standard by states, districts, or federal programs (e.g., ESSA compliance tools)
- Cited across multiple existing hub entries

### Automatic exclusions at source level
- Vendor marketing sites (even when citing research)
- Advocacy organizations whose primary output is opinion, not evidence synthesis
- Sources that explicitly block automated access (Child Trends, RAND robots.txt)
- Sources where no individual resource pages are fetchable (description cannot be verified)

---

## Level 2 — Resource inclusion criteria (per entry)

A specific resource from a qualified source is included if it meets **all**:

1. **Fetchable content**: The page must be fetched and content must be readable. A resource whose page returns 403, 404, or paywall block is dropped — no entry is created. (Playwright may be used for JS-rendered pages; if content is still unreadable, drop the entry.)
2. **Descriptive content available**: The page must have enough text to write a 1–3 sentence description from actual content — not inferred from the title alone.
3. **In scope** (see scope section below).
4. **Published by the source** at the URL being indexed — not a third-party paper *about* the source, not a marketing document citing the source's research.

### Additional threshold by resource type

| Type | Threshold |
|---|---|
| `paper` | Peer-reviewed, or published in a recognized evidence journal (JEDM, JLA, RER, etc.), or from an IES/Campbell/WWC-affiliated venue |
| `report` | Published by an organization with editorial review (not an individual researcher's blog post) |
| `framework` | From a recognized professional organization or research institution; must have a permanent accessible URL |
| `platform` | Actively maintained OR historically significant with documented research use; must have an accessible information page |
| `tool` | Must have documented methodology, validation study, or adoption by a recognized institution |
| `curriculum` | Must have evidence of research-backed development (e.g., OER with efficacy study, IES-funded curriculum) |
| `dataset` | Must be from a government agency, university, or established research org; must be publicly accessible with a documented access path |
| `code` | Must be from a recognized research lab or have documented peer-reviewed publication describing the tool |
| `blog-post` | Only from recognized organizations (IES, EEF, Brookings) on substantive evidence topics; not opinion pieces |

---

## Scope

### In scope
- **K-12 education** — any subject, any country, any instructional context
- **Early childhood** (PreK–3) when directly related to school readiness or learning outcomes
- **Higher education** — undergraduate and graduate when directly related to instruction, assessment, or learning systems
- **Adult/continuing education** when connected to learning engineering methods (ITS, adaptive systems, formative assessment)
- **Learning engineering methods** — A/B testing, intelligent tutoring, NLP for education, automated feedback, learning analytics
- **Education policy and equity** — when grounded in evidence synthesis (not pure advocacy)
- **Datasets** — open datasets from authoritative sources enabling learning research
- **Tools and platforms** — when there is a documented evidence base or the tool is widely used in research contexts

### Out of scope
- **School administration and operations** not directly related to learning outcomes (scheduling, facilities, finance)
- **Workforce development** without an educational component in a K-12 or higher-ed setting
- **Vendor marketing** — even when citing real studies
- **Preprints** without subsequent peer review (unless from an established venue like Annenberg EdWorkingPapers, where the institutional affiliation provides a quality signal)
- **Content older than ~15 years** unless it is foundational/canonical (e.g., How People Learn 2000 is foundational; an obscure 2008 correlational study is not)
- **Pure opinion or commentary** without evidence grounding
- **Resources behind paywalls** with no OA version

---

## Age cutoff rationale

Most repositories apply implicit or explicit age cutoffs. WWC reviews recent studies; EEF's toolkit prioritizes current meta-analyses. The BEE explicitly warns against citing older studies when newer synthesis is available.

Our policy: **resources more than 15 years old require a specific reason to include** — they must be foundational (canonical in the field), explicitly cited as foundational by multiple newer sources in the hub, or represent the only source on a historically important question. When in doubt, prefer the newest synthesis.

---

## What we do NOT do (differentiates us from clearinghouses)

Unlike WWC, EEF, or Evidence for ESSA, this hub does not:
- Rate individual studies for internal validity
- Assign evidence tiers (Strong/Moderate/Promising)
- Require RCTs or QEDs as an inclusion threshold
- Commission or conduct original research synthesis

We rely on source organizations to have done that work. Our curation decision is at the *source* level, not the *study* level. This is the same model as Will Rinehart's policyhub.us and as how ERIC operates as an index rather than a clearinghouse.

---

## Edge cases and judgment calls

Log all non-obvious decisions in `docs/indexing-decisions.md`. Standard edge cases:

| Situation | Decision |
|---|---|
| Resource is cited by a qualified source but published by a third party | Use the third-party publisher's page as the URL and source; do not attribute to the citing source |
| Resource is from a qualified source but is clearly a news/commentary piece | Skip unless from a high-signal source (Brookings) on a substantive evidence topic; flag in indexing-decisions.md |
| Resource is a series or collection (e.g., "4 briefs on AI literacy") | One entry per document; collection-level entries acceptable if no individual URLs exist |
| Resource page is accessible but only shows an abstract | Write description from abstract; set `description_inferred: true` |
| Resource is a well-known framework (SAMR, Bloom's) not published by an org in our source list | Exclude — we index organizations' output, not the field's general canon |
| Vendor publishes an independent study on their product | Include the independent study if published by the independent researcher's institution, not by the vendor |
