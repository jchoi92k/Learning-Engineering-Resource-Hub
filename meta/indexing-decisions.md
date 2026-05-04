# Indexing Decisions Log

> Every arbitrary or judgment-based decision made during indexing is recorded here.
> Purpose: make the editorial process transparent and reproducible.
> If a decision is wrong, fix it here and in llms-full.txt.

---

## Session: 2026-05-01

---

### Numbering restart

**Decision:** Restarted entry numbering at 1 for v2 knowledge base.  
**Why:** The v2 KB is built on a different curation policy (pre-curated sources only, no inference). Legacy entries (1–84) are preserved at docs/legacy/llms-full.txt. Running two numbering schemes in parallel would be confusing; a clean restart makes v2 self-contained.  
**What this means:** Any reference to "entry 1" in this KB means the WWC guide, not the first AIMS entry.

---

### WWC: Which practice guides were selected

**Decision:** Selected 9 of 30 available WWC Practice Guides (entries 1–9).  
**Why (included):**
- #1 Organizing Instruction and Study — directly covers spacing, retrieval practice, worked examples; Kenneth Koedinger is a panel member; core LE methods
- #12 Using Student Achievement Data — formative assessment and data-informed instruction; core LE practice
- #16 Math Problem Solving Gr 4–8 — math focus with Koedinger on panel; LE-relevant
- #18 Teaching Math to Young Children — early childhood math; LE-relevant
- #19 English Learners — ELL is an explicit domain in our tag schema
- #20 Algebra Knowledge — secondary math; LE-relevant
- #25 Technology and Postsecondary Learning — technology-supported learning
- #26 Math Intervention Elementary — intervention-focused math; strong evidence ratings
- #30 Preparing Young Children for School — early childhood; recently updated (2022)

**Why (excluded):**
- Dropout prevention (#9, #24) — outside LE scope
- Turning around low-performing schools (#7) — school improvement, not LE
- Reducing behavior problems (#4) — behavior management, not LE
- Literacy/reading guides (#3, #8, #11, #14, #17, #21, #22, #29) — partially relevant but reading instruction is a different field; can add selectively later
- College completion guides (#23, #27, #28) — postsecondary access, not LE
- Out-of-school time (#10) — outside scope
- Girls in math and science (#5) — equity/pipeline, not LE methods
- School choice (#6 is actually ELL — already included as #19)

**What I could not confirm:** Whether more recent versions of older guides exist. The revision dates shown on the pages reflect what was fetched; some guides may have updated versions not yet on the list page.

---

### WWC: Type assignment

**Decision:** Assigned type `framework` to all WWC Practice Guides.  
**Why:** WWC Practice Guides are not research reports of a single study — they are syntheses of evidence distilled into actionable recommendations with implementation steps. The IES page describes them as "evidence-based recommendations for educators." `framework` is the closest type in our schema. `report` would imply a single research study or policy analysis.  
**Alternative considered:** `report` — rejected because these are prescriptive guidance documents, not descriptive research reports.

---

### WWC: Tag `intelligent-tutoring` on entry 8

**Decision:** Added `intelligent-tutoring` to entry 8 (Math Intervention Elementary, WWC #26).  
**Why:** The guide covers systematic instruction for students with disabilities, timed fluency activities, and number line instruction — methods directly used in ITS implementations. However, the guide itself does not mention ITS or technology. This tag reflects topical overlap, not explicit content.  
**Risk:** Could mislead an agent into thinking this guide covers ITS software. Removed on reflection — the tag is not supported by the page content.  
**Final decision:** Removed `intelligent-tutoring` from entry 8. Tags reflect only what the document explicitly addresses.

---

### CAST UDL: URL choice

**Decision:** Used `https://udlguidelines.cast.org` as the URL, not a direct PDF download link.  
**Why:** The interactive web tool at this URL is the primary authoritative access point described on the page. The PDF is a "graphic organizer" download, not the canonical document. The URL `udlguidelines.cast.org` is stable and loads the full framework.  
**What I could not confirm:** The PDF download URL (not fetched directly). The page references a "downloads page" but I did not follow that link.

---

### CAST UDL: New tag `inclusive-design`

**Decision:** Added `inclusive-design` as a new tag not in the original schema.  
**Why:** UDL is explicitly a framework for inclusive design of learning environments; no existing tag covers this. `cognitive-science` and `learning-engineering` are present but insufficient to represent the disability/accessibility dimension of UDL 3.0.  
**Schema update needed:** Add `inclusive-design` to the Topic category in schema.md.

---

### UNESCO: UNESDOC 403 handling

**Decision:** Entries 12 and 13 (AI Competency Frameworks for students and teachers) use the UNESCO article page URL, not the direct UNESDOC PDF URL, because UNESDOC returned 403 during the audit.  
**Why:** The article page at `unesco.org/en/articles/what-you-need-know-about-unescos-new-ai-competency-frameworks-students-and-teachers` is accessible, describes both frameworks in detail (authors, year, competency areas), and links to the direct downloads. This is not an inference — I read the description from that page.  
**What I could not confirm:** Whether the UNESDOC PDF URLs (pf0000391105_eng, pf0000391104_eng) will be accessible to end users (they may require browser-level access that differs from WebFetch). Noted in the entry descriptions.  
**Alternative considered:** Dropping both entries (strict no-inference policy) — rejected because I have confirmed factual content from an accessible secondary page, not inference from a title.

---

### UNESCO: Entries 12 and 13 share a URL

**Decision:** Both the student framework (entry 12) and teacher framework (entry 13) point to the same article URL.  
**Why:** The UNESDOC URLs for each are blocked, and the single article page describes both documents together. Two separate entries are warranted because they are distinct documents with different authors and audiences.  
**Risk:** An agent fetching entry 12's URL will see content about both frameworks, not just the student one. The descriptions in each entry are specific to the relevant document to mitigate this.

---

### UNESCO: Recommendation on AI Ethics — URL choice

**Decision:** Used the UNESCO article page URL for entry 11 (AI Ethics Recommendation), not the UNESDOC document URL.  
**Why:** The article page was fetched and returned confirmed content (title, year, scope, addressees, summary). The UNESDOC URL was not attempted for this document because the pattern of 403s on UNESDOC suggested it would also fail.  
**What I could not confirm:** The UNESDOC direct document URL for this document was not verified accessible.

---

### UNESCO: Which documents were excluded

**Decision:** Did not index Beijing Consensus (#pf0000368303) or the 2022 International Forum Analytical Report (#pf0000386162) in this session.  
**Why:** UNESDOC returned 403 for all direct document URLs. I have only the titles and URLs for these documents — no confirmed description content. Under the no-inference policy, I cannot write descriptions from titles alone. They are in the sources-log for future re-attempt via browser or alternative access.  
**What I could not confirm:** Whether descriptions are available on secondary landing pages for these documents.

---

### New tags added to schema

The following tags were used in v2 entries but are not in the original schema. Schema.md needs updating:

| Tag | Category | Justification |
|---|---|---|
| `wwc` | Affiliation | What Works Clearinghouse is a distinct producing organization |
| `unesco` | Affiliation | UNESCO is a distinct producing organization |
| `cast` | Affiliation | CAST is a distinct producing organization |
| `ai-ethics` | Topic | Covers AI ethics frameworks and guidance (distinct from `ai-policy` which is legislative/regulatory) |
| `inclusive-design` | Topic | UDL and accessibility-focused instructional design |

---

## Session: 2026-05-01 (continued — entries 14–20)

---

### Carnegie Learning: RAND 2X study and ClearMath brochure excluded

**Decision:** Did not index the RAND 2X study flyer (CDN PDF) or the ClearMath Elementary brochure (CDN PDF).  
**Why:** Both URLs point to Carnegie Learning CDN marketing PDFs. The RAND 2X study is an independent DoE-funded study; the authoritative source would be the RAND Corporation publication, not CL's one-page summary flyer. The ClearMath brochure is unambiguously a marketing document. Indexing either would be indexing CL's characterization of research, not the research itself.  
**What I could not confirm:** The RAND Corporation primary publication URL for the 2X study. If found, that entry should be added under source="RAND Corporation" pointing to the RAND report directly.

---

### Carnegie Learning ESSA Math: url_confirmed: false

**Decision:** Marked entry 14 (ESSA Math report) as `url_confirmed: false`.  
**Why:** The PDF URL was found on the CL research page but the CDN PDF was not directly fetched. Content verified only from the research page listing text. Consistent with the no-inference policy: description sourced from fetched content (CL research page), not from the PDF itself.

---

### EMERALDS: source attribution

**Decision:** Listed source as "Carnegie Mellon University / Educational Testing Service" rather than "Carnegie Learning" or "Achieve the Core."  
**Why:** EMERALDS is a research study conducted by CMU HCII and ETS under PI David C. Geary. The study happens to examine MATHia usage data, but the producing organizations are the academic institutions. Achieve the Core is the host, not the producer. Carnegie Learning provided data access but is not the research author.  
**Risk:** The CMU/ETS source attribution may not match what users expect when navigating from the CL research page. Mitigated by including `carnegie-learning` in the tags.

---

### Lenses on Literature: using Evidence for ESSA as source

**Decision:** Used `evidenceforessa.org/program/lenses-on-literature/` as the URL and "Evidence for ESSA" as the source, rather than the Carnegie Learning marketing brochure.  
**Why:** Evidence for ESSA (Johns Hopkins University) is an independent evidence clearinghouse. The CL brochure is their own marketing; the Evidence for ESSA page is an independent third-party review. Same product, but the independent review is the more credible source for evidence claims.  
**Alternative considered:** CDN brochure URL — rejected for the same reason as the RAND flyer.

---

### Digital Promise: DSpace 403 handling

**Decision:** Entries 18–20 (Digital Promise reports) use DSpace URLs as the canonical resource URL but are marked `url_confirmed: false` and `description_inferred: true`.  
**Why:** All DSpace URL patterns (both `/items/` and `/handle/`) returned 403 during audit. The digitalpromise.org/our-reports/ listing page is accessible and provides brief descriptions for each report. This is sufficient to establish the resource exists and what it covers, but does not meet the "full content readable" standard.  
**What this means for users:** The DSpace URLs may be accessible via browser even though they blocked WebFetch. These entries should be re-audited once DSpace access is available.

---

### New tag: `jedm`

**Decision:** Added `jedm` to the Affiliation tag category in schema.md.  
**Why:** Journal of Educational Data Mining is a distinct producing venue analogous to `wwc` for WWC guides. Tagging JEDM papers with `jedm` enables filtering all journal entries by source. The journal itself is the venue; authors' institutional affiliations are separate (e.g., Baker/WPI, Yacef/Sydney are not tagged separately since they are not recurring organizational sources in this hub).

---

### JEDM article ID discovery

**Decision:** Used article/view/8 for Baker & Yacef 2009 without systematic enumeration of all JEDM IDs.  
**Why:** ID 8 was confirmed to return the Baker & Yacef article via direct fetch. JEDM article IDs are not sequential from 1 (some IDs return 404 or redirect to login). Systematic ID enumeration is not warranted for curating a small set of foundational papers. Future JEDM entries should use the volume/issue browse pages to identify candidate articles, then fetch article/view/[ID] to confirm.

---

## Session: 2026-05-01 (WWC scope revision — entries 21–39)

---

### WWC scope: all 30 guides in scope

**Decision:** Revised from 9 selected guides to all 29 accessible guides (guide #13 returns 500 — likely no such guide; guide #9 skipped because #24 is the 2017 updated version).  
**Why:** The original 9-guide selection applied a secondary "learning engineering methods" filter on top of WWC's own curation. This was inconsistent with the hub's actual scope. The legacy index (AIMS Collaboratory) included school discipline, student belonging, attendance, and other topics far beyond narrow LE methods — the hub's scope is broadly evidence-based education, not only LE methods. WWC is an authoritative pre-curated source; their 30 guides define the domain they consider worth recommending. Applying a further filter is second-guessing their editorial judgment without a principled basis.  
**What changed:** Literacy guides (#3, #6, #8, #14, #17, #21, #22, #29), school turnaround (#7), behavior (#4), out-of-school time (#10), college navigation (#11), fractions (#15), girls in STEM (#5), postsecondary (#23, #27, #28), and dropout prevention (#24) all added.

---

### WWC guide #9 vs. #24: dropout prevention version choice

**Decision:** Indexed #24 (Preventing Dropout in Secondary Schools, 2017) and skipped #9 (Dropout Prevention, 2008).  
**Why:** The fetch of PracticeGuide/9 explicitly states it was "superseded by an updated 2017 version incorporating nine additional years of research." PracticeGuide/24 is the current authoritative version. Indexing both would create a duplicate with stale recommendations for the same topic.

---

### WWC guide #13: 500 error

**Decision:** No entry for PracticeGuide/13.  
**Why:** Direct fetch returns HTTP 500. No title or content retrievable. This guide may not exist, may have been retired, or may be temporarily unavailable. Under the no-inference policy, an entry cannot be created without confirmed page content.

---

### New tags added (2026-05-01 scope revision)

| Tag | Category | Justification |
|---|---|---|
| `literacy` | Domain | Major instructional domain parallel to `math-education`; needed for 8+ WWC literacy guides |
| `response-to-intervention` | Method | Specific instructional framework used across multiple WWC guides (RtI/MTSS); distinct enough from generic `coaching` or `computer-assisted-learning` |
| `sel` | Topic | Social-emotional learning; needed for WWC behavior and related guides |
| `writing-instruction` | Topic | Distinct subfield within literacy; needed for WWC writing guides |
| `college-access` | Topic | Covers both K-12 college readiness and postsecondary access/completion support |
| `career-readiness` | Topic | Career and technical education at postsecondary level |
| `dropout-prevention` | Topic | Specific policy area with dedicated WWC guide and related research |

---

### Source audit methodology change

**Decision:** Future source assessments must confirm accessibility by fetching an actual source document (a specific report, paper, or framework page), not just a listing or summary page.  
**Why:** Several sources in the original audit were marked ✅ based on listing pages loading, even though individual document pages were inaccessible (403/404). This gave a false sense of accessibility. A source is only useful if the content of specific documents can be retrieved for entry writing.  
**What this means for existing assessments:** Digital Promise (DSpace 403), MDRC (403), AIR (403), RAND (403), Brookings (403/404), Child Trends (404 on documents), and Annenberg (ECONNREFUSED) are all effectively inaccessible for indexing purposes via WebFetch, regardless of whether their homepage loads.

---

## Session: 2026-05-01 (LPI, NAP, CASEL, EdTrust — entries 138–148)

---

### LPI: URL slug discovery

**Decision:** LPI product pages use the slug pattern `learningpolicyinstitute.org/product/[slug]` where slugs are not predictable from titles. Used the `/publications` listing page and `/topic/community-schools` topic page to discover slugs, then fetched each product page directly to confirm content.  
**What this means:** Future LPI indexing should start from topic pages or the publications listing rather than guessing slugs.

---

### NAP: URL pattern change

**Decision:** NAP catalog URLs (`nap.nationalacademies.org/catalog/[ID]`) redirect to `www.nationalacademies.org/publications/[ID]`. Reader URLs (`nap.nationalacademies.org/read/[ID]`) redirect to `www.nationalacademies.org/read/[ID]/chapter/`. Used the confirmed redirect destinations as canonical URLs.  
**What I could not confirm:** Whether `www.nationalacademies.org/publications/[ID]` renders full book metadata for all catalog IDs (confirmed for 24783). The `/read/[ID]/chapter/` URL returns full chapter listing and book metadata.

---

### NAP: Type assignment

**Decision:** Assigned type `report` to both How People Learn volumes.  
**Why:** These are consensus study reports produced by committees convened under the National Academies process — the highest-prestige research synthesis body in the US. `report` is the appropriate type; `framework` would imply prescriptive guidance (like WWC Practice Guides or UDL Guidelines).

---

### CASEL: SEL Framework type assignment

**Decision:** Assigned type `framework` to the CASEL SEL Framework.  
**Why:** The CASEL Wheel defines a competency taxonomy and implementation model — it is prescriptive guidance, not a research report. Consistent with the type assignment for WWC Practice Guides and UDL Guidelines.

---

### EdTrust: URL slug discovery

**Decision:** EdTrust report slugs are not predictable from titles. Discovered correct slugs by fetching `edtrust.org/research/` listing page, which returned three confirmed report URLs for the SEAD-related reports (145–147). Funding Gaps 2018 slug was confirmed directly.  
**Note:** Several slug patterns that seemed reasonable (e.g., including full title words) returned 404. Always discover from a listing or search page rather than constructing slugs.

---

### New affiliation tags added (2026-05-01)

| Tag | Category | Justification |
|---|---|---|
| `lpi` | Affiliation | Learning Policy Institute — distinct producing organization, 4 entries indexed |
| `nap` | Affiliation | National Academies Press — distinct producing organization, 2 entries indexed |
| `edtrust` | Affiliation | The Education Trust — distinct producing organization, 4 entries indexed |
| `casel` | Affiliation | Collaborative for Academic, Social, and Emotional Learning — distinct producing organization, 1 entry indexed |

---

## Session: 2026-05-02

---

### Source discipline rule formalized (Khan Academy incident)

**Decision:** Established a hard source discipline rule: each source is a specific domain/URL with a documented access pattern. Agents collect only what that domain has published on its own site. If the source's own domain is inaccessible, the agent writes a failure header to the staging file and stops — it does not go to external databases (ERIC, NBER, OpenAlex, Kaggle) to find third-party papers *about* or *attributed to* that source.

**Why:** A collection agent fetched 22 entries attributed to Khan Academy, but all were third-party papers from ERIC/NBER citing KA as a study context — not content KA published on their own domain. This violates the source field semantics: `source` must be the organization that published the content at the URL, not the subject of the research.

**What changed:** All 22 KA entries removed. Rule added explicitly to agent-guide.md under "Source discipline rule" section. Khan Academy documented in sources-inventory.md as an access failure (research.khanacademy.org redirects to homepage; no indexable publications listing found).

---

### Playwright adopted as JS-rendering layer

**Decision:** Installed Playwright (Python, MIT license) as the primary tool for JS-rendered pages and bot-blocked sources. Replaces Firecrawl (declined — requires paid API key).

**Why:** Several sources could not be indexed via WebFetch because their pages are JavaScript-rendered SPAs (DSpace/Angular) or behind WAFs. Playwright runs a headless Chromium browser locally with no API costs. Confirmed working on Digital Promise DSpace with `wait_for_selector('ds-item-page')` after `wait_until='networkidle'`.

**Installation:** `pip install playwright && python -m playwright install chromium`

**What this unlocks:** Digital Promise DSpace (previously 100% blocked), and potentially MDRC (WAF may yield to browser user-agent). Does not help with Child Trends (hard Anthropic block) or RAND (robots.txt 403).

---

### Digital Promise: DSpace entries 18–20 fixed

**Decision:** Updated entries 18–20 from `url_confirmed: false, description_inferred: true` to `url_confirmed: true, description_inferred: false`. Descriptions rewritten from actual fetched page content (abstract from DSpace item pages via Playwright).

**Why:** These entries were originally written during the 403-blocked era with descriptions sourced from the DP reports listing page. Playwright now makes the actual item pages accessible. The entries were accurate but didn't meet the full-content standard.

---

### Digital Promise: 27 new entries (364–390)

**Decision:** Indexed 27 Digital Promise reports from their DSpace repository (entries 364–390), prioritizing AI in education, learning sciences, digital learning platforms, multilingual learners, and learning analytics topics.

**Discovery method:** DSpace REST API at `/server/api/discover/search/objects` (accessible via WebFetch, returns JSON) to list all 252 items sorted by date; selected the 27 most in-scope items. Item pages fetched via Playwright.

**Selection criteria:** AI literacy and policy (6 entries), digital learning platforms and R&D infrastructure (5 entries), learning sciences and collaborative learning (5 entries), multilingual/English learner content (2 entries), math instruction (2 entries), futures/skills assessment (2 entries), privacy/equity (2 entries), other (3 entries).

**Excluded:** Workforce development, career pathways, maker learning, and 360 Story Lab content — outside the evidence-based K-12/higher-ed instruction scope.

---

### New resource types: `tool` and `curriculum`

**Decision:** Added `tool` and `curriculum` as new resource types to schema.md and build_tags.py.

**Why:** `tool` was already used by WWC in their own taxonomy (assessment instruments, rubrics). `curriculum` covers instructional materials like OpenSciEd units indexed through Digital Promise entries. Neither fit neatly into the existing types. WWC's own use of "tool" validates the type name.

---


## Session: 2026-05-02 (continued — Brookings drops, dataset batch, inclusion criteria)

---

### Brookings: 3 news pieces removed

**Decision:** Removed entries 5, 11, and 23 within the Brookings batch (absolute entries in range 309–333) — news/commentary pieces rather than research reports.

**Why:** These entries were flagged during collection as news reaction pieces: short opinion posts responding to current events rather than research briefs or analytical reports. Under the inclusion criteria for `report` type, entries must come from organizations with editorial review and must be substantive evidence content. Event-response commentary does not meet this threshold even when published by a credible source like Brookings.

**Result:** Brookings count reduced from 25 to 22. Entry ranges 309–333 now contain 3 gaps.

---

### Dataset batch: 30 entries added (entries 387–416)

**Decision:** Indexed 30 dataset entries from 14 distinct sources (entries 387–416), covering major US federal datasets, international assessments, and learning engineering research datasets.

**Sources included:** NCES suite (NAEP, IPEDS, CCD, ECLS, HSLS:09, ELS:2002, NELS:88, BPS), CRDC (Dept of Education), Urban Institute, National Student Clearinghouse, OECD (PISA, TALIS, PIAAC), IEA (TIMSS, PIRLS), World Bank EdStats, ICPSR, Opportunity Insights, Stanford CEPA (SEDA), CMU LearnLab (DataShop/KDD Cup, LearnSphere), Open University (OULAD), WPI (ASSISTments), Riiid (EdNet), Duolingo (SLAM), NBER, NTPS, NHES, EDFacts (Dept of Education).

**Why 30 target:** Datasets are first-class entries alongside reports and papers. The 30-per-source norm applied to other sources (LPI, EdTrust, JEDM) was applied here to establish meaningful coverage of the dataset landscape.

**Excluded:** Opportunity Insights beyond its single entry — the data page is organized as CSV files by research paper rather than named standalone datasets; no meaningful expansion possible without individual paper-level entries which would require a different source attribution.

---

### Inclusion criteria: two-level framework derived from comparable repository research

**Decision:** Established formal inclusion criteria at two levels: (1) source organization, (2) individual resource. Criteria documented in `docs/inclusion-criteria.md`. Research on 10 comparable repositories documented in `docs/comparable-repositories.md`.

**Key principles adopted:**
- Pre-curated source model: we rate sources, not individual studies. Same model as ERIC (an index, not a clearinghouse).
- Three mandatory source-level gates: editorial accountability, public access, relevance to evidence-based education.
- Resource-level gate: page must be fetchable and descriptive content available — no inference from titles.
- Age cutoff: resources >15 years old require justification (foundational/canonical).
- Developer-created outcome measures excluded (consistent with Evidence for ESSA and BEE).

**Sources surveyed:** WWC, EEF, Evidence for ESSA, BEE, Campbell Collaboration, ERIC, EdResearch for Action, Results for America, IES Practice Guides, NESTA.

---

## Session: 2026-05-03

---

### NCES expansion: 20 additional survey entries (entries 417–436)

**Decision:** Indexed 20 remaining NCES survey programs, bringing NCES total to 30 entries. All pages confirmed accessible (HTTP 200, 900–6900 chars content).

**Surveys added:** NAAL, BTLS, CTE Stats (CTES), MGLS:2017, School Pulse Panel, NPSAS, B&B, SASS, PSS, SSOCS, HS&B, NLS-72, HST, EDSCLS, EDFIN, SLDS, Library Statistics Program, IAP, Locale Studies (formerly ruraled — redirects to annualreports/topical-studies/locale), CPS.

**Redirect handled:** `nces.ed.gov/surveys/ruraled/` permanently redirects to `nces.ed.gov/surveys/annualreports/topical-studies/locale` — entry uses the final destination URL and title ("Education Across America: Cities, Suburbs, Towns, and Rural Areas").

**Why 30 target for NCES:** NCES is the flagship US federal education statistics agency. Treating it with the same 30-entry target as LPI, EdTrust, and JEDM gives it proportional representation. The suite of ~30 named survey programs maps cleanly to ~30 entries.

**Excluded from this pass:** Higher-education-specific financial surveys and small specialized collections with minimal content. All excluded surveys either had sparse landing pages or were subcomponents of already-indexed programs.

---
### IEA: 4 new entries (437–440)

**Decision:** Indexed 4 IEA study programs not previously in the hub: ICCS (437), ICILS (438), TEDS-M (439), REDS (440).

**Already indexed and skipped:** TIMSS (399), PIRLS (400), TALIS (412 — under OECD), PIAAC (413 — under OECD).

**TIMSS Advanced dropped:** No dedicated URL exists — it is described inline on the main TIMSS page (`iea.nl/studies/iea/timss`), which is already entry 399. Creating a second entry at the same URL would violate the one-entry-per-URL rule.

**TEDS-M age caveat:** Data collection was 2007–08 (18 years old). Included because it is the only international comparative study of mathematics teacher education, is still actively cited, and the dataset remains publicly accessible via IEA's data repository. Qualifies under the "foundational/canonical" exception to the 15-year age cutoff.

**REDS scope note:** Covers 11 nations including several developing countries outside typical OECD scope. Included because it is an IEA-published dataset with a clean DOI and public download, and the COVID-19 educational disruption topic is broadly relevant.

---

### US Dept of Education AI reports: access failure

**Decision:** Did not index. No entries created.

**What was tried:** `tech.ed.gov` (301 → ed.gov homepage), `ed.gov/about/offices/list/os/technology/ai-future-of-teaching-learning.html` (404), `ed.gov/about/ed-overview/ed-artificial-intelligence` (404), `ed.gov/laws-and-policy/laws-progs-initiatives/artificial-intelligence` (404), `ed.gov/technology` (404), direct PDF URLs — accessible but WebFetch returns binary data, not parseable text.

**Known working PDF URL:** `https://www.ed.gov/documents/ai-report/ai-report.pdf` — the 2023 "Artificial Intelligence and the Future of Teaching and Learning" report. Confirmed it resolves (1.8MB PDF) but cannot be read by WebFetch.

**Why stopped:** No HTML landing page found. ed.gov was restructured and tech.ed.gov eliminated. Forcing PDF-to-text parsing would require a convoluted pipeline inconsistent with our clean-URL-pattern requirement. Retry requires browser navigation to find current landing page URL, or a PDF parsing tool.

---

### CCSSO AI guidance: access failure

**Decision:** Did not index. No entries created.

**What was tried:** `ccsso.org/resource-library?topic=ai` (404), `ccsso.org/resource-library?search=artificial+intelligence` (404), `ccsso.org/resource-library/artificial-intelligence-k-12-education-framework-for-state-policies` (404), `ccsso.org/blog/ccsso-artificial-intelligence` (404), `ccsso.org/publications` (404), `ccsso.org/resources` (404), `ccsso.org/ai` (404), `ccsso.org` homepage (no AI links visible).

**Robots.txt:** Permissive (standard Drupal). No crawling restrictions on content pages.

**Why stopped:** All slug patterns returned 404. The resource library appears to require JS rendering (Drupal + client-side routing) and the URL pattern is not guessable from titles. Retry via: (1) Playwright + `ccsso.org/resource-library` to render the listing and extract URLs, or (2) `ccsso.org/sitemap.xml` if it exists.

---

### Duolingo inclusion decision (2026-05-03)

**Decision:** Retain Duolingo entries (existing entry 410, plus the spaced repetition dataset from the 2026-05-03 survey). Governing rule: Duolingo datasets qualify **only** when released as part of a peer-reviewed academic venue (workshop shared task, conference paper with peer review, or equivalent). Duolingo blog posts, language learning research reports, and internal studies do not qualify.

**Why:** Duolingo is a commercial vendor, and the inclusion criteria excludes "self-published vendor content." However, the specific datasets indexed were released through external peer-reviewed venues: entry 410 (SLAM) via the BEA workshop; the spaced repetition dataset via ACL 2016. The editorial gatekeeper for both is the peer-review process of the venue, not Duolingo itself. This is analogous to a Google Research dataset released at NeurIPS — vendor-produced but academically vetted. The rule requires the peer-review connection to be explicit and traceable.

**How to apply:** Before adding any new Duolingo entry, confirm: (a) the dataset accompanied a peer-reviewed publication at a named venue, (b) the venue is identifiable from the page content, (c) the dataset has a DOI or is hosted at a recognized data archive. If these conditions are not met, drop the entry.

---

### Session: 2026-05-03

---

### US Dept of Ed datasets: Playwright recon + 2 new entries (441–442)

**Decision:** Indexed 2 US Dept of Education dataset resources via Playwright rendering.

**Recon method:** Playwright (headless Chromium, `wait_until="networkidle"`) on four candidate pages. Results:
- `collegescorecard.ed.gov/data/` — rendered fully (3022 chars); rich content on downloads and API
- `civilrightsdata.ed.gov` — rendered fully (3656 chars); already indexed as entry 395, skipped
- `data.ed.gov` — CloudFront 403 blocks even Playwright; dead end
- `covid-relief-data.ed.gov` — rendered fully (4774 chars); ESF grantee data with API

**College Scorecard (441):** Institution and field-of-study data covering 1996–2023, public REST API, OPEID-UNITID crosswalk files. Widely used in higher-ed research. URL: `collegescorecard.ed.gov/data/`.

**ESF COVID Relief (442):** Tracks $276B in ESSER/HEER/EANS/GEER awards and expenditures at grantee level; public API; bulk data downloads. Useful for COVID educational disruption research. URL: `covid-relief-data.ed.gov`.

**Dollar-sign stripping bug (fixed):** PowerShell here-strings interpolate `$` as variable prefixes, stripping dollar amounts from the ESF description. Fixed by using the Edit tool to restore the correct text after detecting the parse count mismatch (build showed 441 instead of 442). Future PowerShell appends with dollar signs: use single-quoted here-strings `@'...'@` or escape as `` `$ ``.

---

### Dataset source coverage: sampling artifact vs. architecture (2026-05-03)

**Decision:** No architecture change yet. Architecture decision deferred pending user direction.

**Context:** After the 2026-05-03 dataset survey expansion (entries 387–487), WWC intervention reports represent roughly 20% of total entries but only a fraction of dataset entries — yet the concern raised was that no single source should dominate 80%+ of a category. The actual concern is about *coverage breadth*, not architecture.

**Root cause:** The asymmetry is a sampling artifact. The hub has ~29 WWC intervention reports indexed and ~481 remaining. Other sources that appear small (JEDM, JLA, EdTrust, Evidence for ESSA) each have hundreds of unindexed resources. The 20% subsample formula and per-session caps create the appearance that these sources have thin catalogs, when in fact they are simply undersampled.

**Coverage note:** WWC intervention reports alone have ~619 total, of which ~481 are unindexed. Evidence for ESSA has hundreds of Moderate + Promising tier programs not yet indexed. JEDM and JLA each have ~10+ volumes with 5–10 papers each beyond what's indexed. The hub at 487 entries is sampling the tip of several large catalogs.

**Implication for expansion:** The next logical expansions (in rough priority) are WWC intervention reports, Evidence for ESSA (Moderate + Promising tiers), JEDM/JLA volumes beyond what's indexed, and Digital Promise (222 unindexed items). These would substantially rebalance the coverage distribution without any architecture change.

---

### Architecture: flat-file scaling ceiling (2026-05-03)

**Decision:** No changes to architecture yet. Documented in `docs/llm-wiki-landscape.md` under "Scaling Architecture." Decision pending user direction.

**Discussion:** At 487 entries (`llms-full.txt` ~7,000 lines), the flat-file source-of-truth is working. The concern is the ceiling: at ~2,000 entries (~29,000 lines) agents loading the full file pay high token costs; at 5,000+ entries the file becomes unwieldy for diffs, manual edits, and context-window fetches.

**Field standard finding** (from research into OpenAlex, Context7, Hugging Face, AI2): The consensus pattern at scale is to flip the source of truth from a growing flat file to either (a) per-item structured files (YAML/JSON per entry, flat files generated on build — the Hugging Face model) or (b) a database with generated exports (the OpenAlex model). Projects that delay this flip face painful migrations.

**Options summarized:**
- A: Shard `llms-full.txt` into per-source files — low effort, buys time
- B: Per-entry YAML/JSON files as source of truth, flat files generated — medium effort, field standard
- C: Database + REST API — high effort, appropriate only at much larger scale

**User has a solution in mind.** Architecture decisions are documented in full in `docs/llm-wiki-landscape.md`.

---

### Architecture revised: LLM-native framing changes the recommendation (2026-05-03)

**Decision:** No changes to architecture yet. Earlier recommendation (Option B: per-entry files) was the right general software-engineering answer but not the right LLM-native answer.

**Correction:** Follow-up research (Knows/knows.academy, arxiv:2604.17309; Karpathy wiki pattern) shows that for a hub whose primary consumer is LLM agents via WebFetch, flat files remain the right choice significantly longer than for human-facing or multi-editor projects:

- At 200K token context windows, `llms-full.txt` at ~800 entries fits in a single load — no retrieval layer needed
- Structured YAML per entry (our current format) directly improves agent accuracy 2–3x vs. unstructured text (empirical finding from Knows paper)
- Source-sharding (Option A/B hybrid) is the right evolution path at ~800 entries: split into per-source files, keep a master index
- MCP query layer (wrapping `data.json`) is appropriate for interactive supervised sessions, not required for autonomous agent use
- Vector embeddings / RAG are unjustified below ~5,000 entries with 200K context windows

**Revised option priority for our hub:**
1. A (stay flat): current → ~800 entries
2. B (source-shard): ~800–5,000 entries
3. C (MCP layer): when interactive supervised use grows
4. D (per-entry files): only if hub becomes multi-editor or needs programmatic writes
5. E (RAG): 5,000+ entries

**Most comparable project:** Knows/knows.academy (arxiv:2604.17309) — YAML metadata per research entry, no content hosting, agent-first. Our hub is an independently-arrived-at instance of the same pattern, applied to education research. No direct education-domain analog exists — our hub appears to be novel in that specific combination.

Full analysis in `docs/llm-wiki-landscape.md` under "Scaling Architecture."

---

### Architecture decided: dual-track + per-entry fragments (2026-05-04)

**Decision:** Implement dual-track delivery with per-entry fragment files as source of truth.

**Dual track:**
- Full track: `llms-full.txt` (all entries) + `llms-[source].txt` per-source shards, both with complete YAML + description
- Lean track: `llms-lean-[category].txt` per-domain files, YAML only (no description) — ~12.7× token efficiency for agents scanning before committing to full load

**Source of truth:** Individual fragment files at `entries/[source]/NNNN.md`. All `docs/llms-*.txt`, `data.json`, and `tags/` are generated outputs, committed to repo for static serving.

**GitHub directory limit:** 3,000 entries per directory (hard limit, confirmed at docs.github.com). Source-bucketed subdirectories (`entries/wwc/`, `entries/datasets/`, etc.) stay well under this at any realistic scale.

**Subagent staging:** Subagents write individual files to `docs/staging/entries/`. No absolute-numbering coordination. Build script assigns final IDs on promotion.

Full architecture in `meta/llm-wiki-landscape.md` under "Decided Architecture."

---

### GitHub Pages: requirements and checklist (2026-05-04)

**Status:** `wiki/` renamed to `docs/` — GitHub Pages source is ready.

**Decisions still needed:**
1. Public or private repo? (Free GitHub Pages requires public repo)
2. Custom domain or `username.github.io/repo-name/`?
3. Who is the intended public audience? (affects README, repo description)

**Technical steps:**

1. `git init` in `Educational resources/` (project root)
2. Create `.gitignore` — exclude `__pycache__/`, `*.pyc`, `.firecrawl/`, `wiki/` (old directory, pending deletion)
3. `docs/index.html` confirmed: uses relative `fetch('data.json')`, no hardcoded localhost URLs — GitHub Pages-ready as-is
4. **Build step**: commit generated files (simplest) — push everything including `data.json` and `tags/`; GitHub Pages serves as-is; re-run `build_tags.py` locally and push after each indexing session
5. **Pages source**: `docs/` directory is now in place — GitHub Pages natively serves `/docs` from repo root with no Actions required
6. Push to GitHub, enable Pages in repo Settings → Pages → Source: Deploy from branch → `main` → `/docs`
7. Update `docs/llms.txt` and `meta/agent-guide.md` with the new public URL once known

---