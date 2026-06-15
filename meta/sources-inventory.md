# Sources Inventory

> Map of reputable source hubs for the Learning Engineering Resource Hub.
> Updated 2026-05-21.
>
> **Scope note:** The weekly automation routine (`meta/automation-prompt.md`) actively checks 14 sources. The full corpus draws on 52 distinct source values — the remainder came from manual and backlog indexing runs and are not checked automatically.

---

## Curation philosophy

This hub indexes **pre-curated content** — collections where an authoritative organization has already done the selection work. We trust their editorial judgment and index from their lists.

This is how Will Rinehart built policyhub.us: he didn't query academic databases and filter down. He identified authoritative organizations and indexed what they'd already surfaced as worth reading.

**OpenAlex / Semantic Scholar are not primary sources here.** They are a utility layer: if a pre-curated entry points to a paper whose abstract isn't on the source page (paywalled, minimal landing page), query the API by DOI to retrieve the abstract. That's all they're used for.

**Scope reminder:** The hub covers all resource types — not just papers. Platforms, datasets, frameworks, policy documents, PD resources, and code repositories are equally valid entries.

---

## Pre-curated sources, by type

### Evidence reviews & research summaries

**What Works Clearinghouse (WWC)**
- URL: https://ies.ed.gov/ncee/wwc/
- What it is: IES's gold-standard evidence reviews. Practice Guides (expert recommendations) + Intervention Reports (program-level evaluations).
- Why pre-curated: IES applies rigorous inclusion criteria. Every report represents a deliberate editorial decision.
- Content types: `framework`, `report`
- Access: Open HTML. Practice Guides at PracticeGuide/[N]. Individual Intervention Reports at Intervention/[slug] — but the listing page is JS-rendered; slugs must be discovered manually or via sitemap.
- **Indexed:** 207 total entries. All 29 Practice Guides complete. ~178 intervention reports indexed.
- **Remaining:** ~441 intervention reports (619 total confirmed by page counter). URL pattern `/ncee/wwc/InterventionReport/[ID]` confirmed working; remaining IDs require systematic discovery.
- Scale: Practice Guides complete. Intervention Reports ~29% coverage.

**IES Research Summaries / REL Products**
- URL: https://ies.ed.gov/ncee/rel/
- What it is: Regional Educational Lab products — practitioner-facing research summaries, toolkits, and implementation guides from all 10 REL regions.
- Why pre-curated: IES-commissioned, practitioner-oriented. Bridges research and practice.
- Content types: `report`, `framework`
- Access: ✅ Confirmed — open HTML + PDFs. URL pattern: `ies.ed.gov/ncee/rel/Products/Publication/[ID]`. Discover via regional listing pages at `ies.ed.gov/ncee/rel/regions/[region]`.
- **Indexed:** 30 reports. Coverage: all 10 REL regions; topics include math achievement, literacy, college access, chronic absenteeism, English learners, early childhood, SEL.
- Scale: Active. Each region publishes dozens of reports; current coverage is a curated sample.

**Learning Policy Institute (LPI)**
- URL: https://learningpolicyinstitute.org/
- What it is: Non-partisan education research org focusing on teacher quality, school design, early childhood, and equity. All reports freely downloadable.
- Why pre-curated: Reports commissioned and peer-reviewed by LPI. Quality signal: major foundation funding (Gates, Hewlett, Carnegie, etc.).
- Content types: `report`
- Access: ✅ Confirmed — product pages load fully, PDFs freely downloadable without login. Slug pattern: `learningpolicyinstitute.org/product/[slug]` — discover slugs from listing or topic pages, not by guessing.
- **Indexed:** 36 reports. Coverage: teacher workforce, early childhood, community schools, school funding, assessment, English learners, equity/integration, school discipline.
- Scale: Active. Could expand further; strong topic pages include `/topic/teaching-profession` and `/topic/broader-learning`.

**National Academies Press (NAP)**
- URL: https://www.nationalacademies.org/ (and nap.nationalacademies.org)
- What it is: Consensus study reports from the National Academies of Sciences, Engineering, and Medicine. The highest-prestige research synthesis body in the US.
- Why pre-curated: Committees convened by Congress. Quality signal: consensus process, top researchers, NSF/federal funding.
- Content types: `report`, `framework`
- Access: ✅ Confirmed — free online reading (no account required); free PDF download. URL pattern: `nap.nationalacademies.org/read/[ID]` → redirects to `www.nationalacademies.org/read/[ID]/chapter/`. Catalog IDs discoverable at `nap.nationalacademies.org`.
- **Indexed:** 2 reports (entries 142–143): How People Learn (2000), How People Learn II (2018).
- Scale: 3–8 landmark reports total. Remaining candidates: Transforming the Workforce for Children Birth Through Age 8 (2015), Science of Learning and Development reports.

**Education Trust (EdTrust)**
- URL: https://edtrust.org/
- What it is: Research and advocacy org focused on equity in K-12 and higher education. Evidence-based briefs on opportunity gaps, teacher diversity, college access.
- Why pre-curated: Reports are independently researched, peer-reviewed, widely cited by policymakers.
- Content types: `report`
- Access: ✅ Confirmed — two URL patterns: `edtrust.org/resource/[slug]` and `edtrust.org/rti/[slug]`. Slugs not predictable from titles. Best discovery: `edtrust.org/research-tools-and-i-sitemap.xml` (282 RTI URLs).
- **Indexed:** 31 reports. Coverage: K-12 equity/access, advanced coursework, school discipline, chronic absenteeism, assessment, higher ed affordability, student debt, teacher diversity.
- Scale: Active. Rich source with 282+ RTI URLs available if expanding further.

**Evidence for ESSA (Johns Hopkins University)**
- URL: https://evidenceforessa.org/
- What it is: Independent evidence clearinghouse rating K-12 programs (reading, math, SEL, attendance) against ESSA evidence standards. Ratings: Strong, Moderate, Promising, Demonstrates a Rationale.
- Why pre-curated: Independent third-party reviews — more credible than vendor-produced efficacy claims. Used by districts for program selection decisions.
- Content types: `report` (each page is an evidence review of a program)
- Access: ✅ Confirmed — open HTML. URL pattern: `evidenceforessa.org/program/[slug]`. Sitemap at `evidenceforessa.org/sitemap.xml` lists 400+ program slugs. Category listings (`/programs/reading`, `/programs/math`) filter to rated programs only.
- **Indexed:** 79 program reviews. Strong and Moderate tiers covered. Coverage: reading/literacy, math, SEL, attendance programs.
- Scale: Active. Promising and Demonstrates a Rationale tiers remain. 400+ slugs in sitemap.

**Brookings Brown Center on Education Policy**
- URL: https://www.brookings.edu/ (filter to Brown Center content via sitemap)
- What it is: The Brookings Institution's education policy research arm. Annual Brown Center Report, plus research briefs on student achievement, curriculum, assessment, and equity.
- Why pre-curated: Brookings is one of the most cited US think tanks. Education content is rigorous and widely used in policy.
- Content types: `report`, `paper`
- Access: ✅ Confirmed — articles load (sitemap at `brookings.edu/sitemap_index.xml`; articles at `brookings.edu/articles/[slug]`). Earlier 403/404 errors were bad URLs, not blocking.
- Caveat: Sitemap contains all Brookings content (not education-specific); need to curate manually from Brown Center listings.
- **Indexed:** 22 reports. Coverage: math achievement, reading, curriculum quality, test scores, teacher policy, equity.
- Scale: Active. Many more Brown Center briefs available; current set is a curated sample.

**Campbell Collaboration**
- URL: https://campbellcollaboration.org/
- What it is: International organization producing systematic reviews in education, social welfare, crime and justice, and international development. Education coordinating group covers K-12 and higher ed.
- Why pre-curated: Systematic reviews; meets GRADE and EPPI Centre standards. Quality signal = funded by Norwegian Research Council and multiple international governments.
- Content types: `report` (systematic reviews)
- Access: ✅ Confirmed — education review pages accessible. URL pattern: `campbellcollaboration.org/better-evidence/education-[slug].html`. Browse from `/our-work/education/` listing or `/better-evidence/` search.
- **Indexed:** 45 systematic reviews. Coverage: reading/literacy, math, SEL, attendance, school choice, tutoring, early childhood, professional development.
- Scale: Active. 52 total education reviews; 7 remaining.

**TNTP**
- URL: https://tntp.org/publications/
- What it is: Research and advocacy org focused on teacher effectiveness, curriculum quality, and opportunity gaps for students in high-need schools.
- Content types: `report`
- Access: JS-paginated (4 pages, 36 total). WebFetch only sees page 1 (10 items). Use `scripts/playwright_scrape.py` for full listing.
- **Indexed:** 36 reports. Coverage: teacher effectiveness, curriculum quality, learning acceleration, equity.
- Scale: Complete — all 36 publications indexed.

**Mathematica**
- URL: https://mathematica.org/evidence?focusArea=Education&contentType=Publication
- What it is: IES-funded RCTs, quasi-experimental studies, and evidence reviews on K-12 and higher-education programs.
- Content types: `report`
- Access: JS-rendered listing (Coveo search). WebFetch sees partial set. Full catalog via Coveo API (fragile — skip in routine; use manual batches).
- **Indexed:** 35 reports. Coverage: early childhood programs, K-12 interventions, postsecondary access, workforce-linked education.
- Scale: Active. ~693 education publications available; current coverage is an initial sample.

**WestEd**
- URL: https://wested.org/resources/?type=research-evaluation
- What it is: Federal regional lab. Research and evaluation on K-12 learning, educator effectiveness, and equity.
- Content types: `report`
- Access: ✅ Confirmed via WebFetch.
- **Indexed:** 14 reports. Coverage: literacy, math, equity, professional development, early childhood.
- Scale: Active. Many more publications available.

**UChicago Consortium on School Research**
- URL: https://consortium.uchicago.edu/publications
- What it is: Independent research center focused on Chicago Public Schools and broader K-12 school improvement — attendance, college readiness, school culture, equity.
- Content types: `report`
- Access: ✅ Confirmed via WebFetch. Slug pattern: `consortium.uchicago.edu/publications/[slug]`.
- **Indexed:** 31 reports. Coverage: attendance, college access, school culture, high school graduation, equity.
- Scale: Active. 319 publications total; significant backlog remaining.

**CREDO at Stanford**
- URL: https://credo.stanford.edu/research-reports/report-finder/
- What it is: Center for Research on Education Outcomes — charter school effectiveness studies and broader K-12 program evaluations.
- Content types: `report`
- Access: ✅ Confirmed.
- **Indexed:** 9 reports. Coverage: charter school effectiveness, urban education, virtual learning.
- Scale: Near-complete — small catalog (~9 total reports).

**NWEA Research**
- URL: https://www.nwea.org/research/ (sitemap: `nwea.org/publication-sitemap.xml`)
- What it is: MAP Growth longitudinal research, academic recovery studies, and learning loss data. Widely cited in policy and practice.
- Content types: `report`, `article`
- Access: ✅ Confirmed via publication sitemap (prefer over JS-rendered listing).
- **Indexed:** 70 entries. Corpus label: `"NWEA Research"`.
- Scale: Active. Sitemap has 200+ publications.

**AERA (American Educational Research Association) — Reviews of Research**
- URL: https://www.aera.net/Publications/Journals/Review-of-Educational-Research
- What it is: Review of Educational Research — meta-analyses and literature reviews.
- Access: Partially paywalled. Select open-access articles accessible. Use DOI + Semantic Scholar for abstracts on paywalled entries.
- Scale: Curate 5–10 landmark review articles, not systematic indexing.

**Horizon Report (EDUCAUSE)**
- URL: https://www.educause.edu/horizon-report
- What it is: Annual landscape scan of emerging technologies in higher ed (and K-12 edition). Widely cited, widely read.
- Content types: `report`
- Access: Free PDF download. New edition each year.
- Scale: One entry per annual edition — the report itself is the unit.

---

### AI policy & guidance

**CoSN (Consortium for School Networking)**
- URL: https://cosn.org/ai
- Already indexed: Entries 82–84 (TeachAI toolkit, Operational AI 2025, K-12 GenAI Maturity Tool).
- Monitor for: New guidance documents as AI policy evolves.
- Content types: `framework`, `report`

**CCSSO (Council of Chief State School Officers)**
- URL: https://ccsso.org
- What it is: National organization of state education commissioners. Publishes AI guidance for state systems.
- Why valuable: Policy-facing; represents state-level adoption decisions.
- Content types: `report`, `framework`
- Access: ❌ Access failure 2026-05-03. Robots.txt is permissive (standard Drupal). However, all resource-library slug patterns tried returned 404. No sitemap or listing page found via WebFetch. The site appears to use JS-rendered navigation for its resource library. Retry via Playwright or by locating a sitemap at `ccsso.org/sitemap.xml`.

**UNESCO — AI in Education**
- URL: https://www.unesco.org/en/digital-education/artificial-intelligence
- What it is: UNESCO's framework and guidance documents on AI in education globally.
- Why valuable: International scope; foundational policy framing documents.
- Content types: `framework`, `report`
- Access: Open. Multiple PDFs.

**ISTE (International Society for Technology in Education)**
- URL: https://iste.org/ai
- What it is: AI in education standards, policy briefs, practitioner guidance.
- Content types: `framework`, `report`
- Access: Mix of open and member-gated. Focus on open.

**US Dept of Education — AI guidance**
- URL: https://ed.gov
- What it is: Federal AI-in-education reports, including the 2023 report "Artificial Intelligence and the Future of Teaching and Learning" (Office of Educational Technology) and subsequent guidance.
- Access: ❌ Access failure 2026-05-03. `tech.ed.gov` permanently redirected away (301 → ed.gov homepage). No `/technology/` or `/ai/` listing page found. Direct PDF URLs (`/documents/ai-report/ai-report.pdf`, `/sites/ed/files/documents/ai-report/ai-report.pdf`) resolve as binary PDF — WebFetch cannot parse. Known PDF URL: `https://www.ed.gov/documents/ai-report/ai-report.pdf` (confirmed redirect destination). Retry requires: (1) finding an HTML landing page via browser, or (2) a Playwright + PDF parser pipeline.
- Content types: `report`

**US Dept of Education — Open Datasets**
- URL: https://ed.gov/data (listing), individual dataset subdomains
- What it is: Federal open data assets covering higher ed, K-12, civil rights, and COVID relief.
- Access: Mixed. WebFetch renders `ed.gov/data` listing. JS-rendered dashboards require Playwright.
  - `collegescorecard.ed.gov/data/` — ✅ Playwright renders fully. Institution-level data 1996–2023, field-of-study data, public REST API. Last updated March 2026.
  - `civilrightsdata.ed.gov` — ✅ Playwright renders. Already indexed as entry 395.
  - `covid-relief-data.ed.gov` — ✅ Playwright renders. ESF grantee expenditure data + API.
  - `data.ed.gov` (main portal) — ❌ CloudFront 403 blocks WebFetch and Playwright.
- **Indexed:** College Scorecard (441), ESF COVID Relief (442). CRDC (395) and NAEP (387) already indexed.
- Discovery method: Start from `ed.gov/data` listing page (static, WebFetch-accessible) to find dataset subdomain URLs, then use Playwright for each.

---

### Platforms & tools

**ASSISTments**
- Already indexed: Entry 80.
- Monitor for: New research publications and platform updates.

**Carnegie Learning / MATHia**
- URL: https://www.carnegielearning.com/research/
- What it is: ITS platform with decades of efficacy research. MATHia, LONG+LIVE+MATH, etc.
- Content types: `platform`, `paper`, `report`
- Access: Not yet attempted. Mix of open reports and paywalled journal articles.

**Khan Academy Research / Khanmigo**
- URL: https://research.khanacademy.org
- What it is: KA's published research on personalized learning, Khanmigo AI tutoring, efficacy.
- Content types: `platform`, `paper`
- Access: ❌ Not indexable via WebFetch. `research.khanacademy.org` redirects to `www.khanacademy.org` homepage. `www.khanacademy.org/research` redirects to `early.khanacademy.org` (archived 2015–2018 R&D site; content does not render). `blog.khanacademy.org` is permission-blocked.
- **Do not index third-party papers about KA from ERIC/NBER/journals.** Only index content published directly by KA on their own domain.
- Next step: find whether KA has a dedicated publications or research listing page that is WebFetch-accessible. Check `www.khanacademy.org/about/research` or similar.

**UpGrade (A/B testing platform)**
- URL: https://upgrade.w3.org (or ucsd.edu/upgrade)
- What it is: Open-source A/B testing platform for education research. Used by TLA.
- Content types: `platform`, `code`
- Access: Check current URL — was indexed in AIMS scrape. Confirm still accessible.

**Digital Promise**
- URL: https://digitalpromise.dspacedirect.org
- What it is: Ed-tech research org publishing reports on AI in education, learning sciences, digital equity, computational thinking, and learning platforms. 252 items total in their DSpace repository.
- Why pre-curated: Independent research with strong AI-in-education and learning sciences focus. Publishes practical frameworks and evidence briefs widely cited by practitioners and policymakers.
- Content types: `report`, `framework`
- Access: ✅ Confirmed via Playwright — DSpace 7 Angular SPA; WebFetch returns empty body (202). Must use Playwright with `page.wait_for_selector('ds-item-page')` after `wait_until='networkidle'`.
  - Discovery: REST API at `digitalpromise.dspacedirect.org/server/api/discover/search/objects?scope=8b62a46e-6df8-4871-84f3-cf007fbb0660&dsoType=item&size=50&sort=dc.date.issued,desc` — accessible via WebFetch (returns JSON without JS rendering).
  - Item URLs: `digitalpromise.dspacedirect.org/items/[UUID]` — UUIDs from REST API response.
- **Indexed:** 254 reports. Coverage: AI literacy, AI policy, digital learning platforms, privacy, multilingual learners, learning sciences, math instruction, R&D infrastructure, computational thinking, learner variability.
- Scale: Active. 252+ items available; near-complete. Requires Playwright batches — use `scripts/playwright_scrape.py`.

**Duolingo Research**
- URL: https://research.duolingo.com
- What it is: Published research from Duolingo on language learning, spacing, engagement.
- Content types: `paper`, `report`
- Access: Not yet attempted.

---

### Datasets

**IEA (International Association for the Evaluation of Educational Achievement)**
- URL: https://www.iea.nl/studies
- What it is: International organization coordinating large-scale comparative assessments of student achievement across countries.
- Why pre-curated: Peer-reviewed international studies; widely used in policy and research. Core source for cross-national education data alongside OECD (PISA, TALIS, PIAAC).
- Content types: `dataset`
- Access: ✅ Confirmed. Robots.txt permissive (Drupal, no content restrictions). Study pages at `iea.nl/studies/iea/[slug]`. Data repository pages at `iea.nl/data-tools/repository/[slug]`.
- URL pattern: `https://www.iea.nl/studies/iea/[study-slug]` for active studies; `https://www.iea.nl/data-tools/repository/[slug]` for archived/data-only studies.
- **Indexed:** 6 total — TIMSS (399), PIRLS (400) in initial dataset batch; ICCS (437), ICILS (438), TEDS-M (439), REDS (440) added 2026-05-03.
- **Not indexed:** TIMSS Advanced (no dedicated URL — described inline on TIMSS main page, which is already entry 399). LaNA (developing-country pilot, out of scope). SITES/CIVED (archived, 1990s–2006, too old).
- Scale: Core active studies complete. Monitor for new cycles (ICCS 2027, ICILS 2028).

**PSLC DataShop / LearnSphere**
- URL: https://learnsphere.org/ and https://pslcdatashop.web.cmu.edu/KDDCup/
- Already indexed: Entries 405–406 (LearnSphere infrastructure, KDD Cup 2010 challenge dataset).
- Content types: `dataset`
- Access: ✅ LearnSphere homepage accessible. DataShop main page times out; use specific dataset pages (e.g., /KDDCup/).

**NCES (National Center for Education Statistics) open datasets**
- URL: https://nces.ed.gov/
- What it is: Flagship US federal education statistics agency. Maintains a suite of nationally representative longitudinal studies and administrative data collections.
- Content types: `dataset`
- Access: ✅ All NCES survey pages accessible (nces.ed.gov/surveys/[name]/).
- **Indexed:** 30 datasets total — 10 in initial batch + 20 in NCES expansion (2026-05-03):
  - Initial batch (entries 387–394, 414–415): NAEP, IPEDS, CCD, ECLS, HSLS:09, ELS:2002, NELS:88, BPS, NTPS, NHES
  - Expansion batch (entries 417–436): NAAL, BTLS, CTE Stats, MGLS:2017, School Pulse Panel, NPSAS, B&B, SASS, PSS, SSOCS, HS&B, NLS-72, HST, EDSCLS, EDFIN, SLDS, Library Statistics, IAP, Locale Studies, CPS
- Scale: Core NCES suite complete at ~30 entries. Next candidate sources: IEA (TIMSS/PIRLS/ICCS/ICILS cycles), DataShop (catalog discovery needed), ASSISTments public releases.

**Additional indexed dataset sources (entries 395–416)**

| Entry | Dataset | Source |
|---|---|---|
| 395 | Civil Rights Data Collection (CRDC) | U.S. Dept. of Education Office for Civil Rights |
| 396 | Urban Institute Education Data Explorer | Urban Institute |
| 397 | National Student Clearinghouse Research Center | National Student Clearinghouse |
| 398 | PISA | OECD |
| 399 | TIMSS | IEA |
| 400 | PIRLS 2021 | IEA |
| 401 | World Bank EdStats | World Bank |
| 402 | ICPSR Education Research Studies | ICPSR (U. Michigan) |
| 403 | Opportunity Insights Education and Mobility Data | Harvard University |
| 404 | Stanford Education Data Archive (SEDA) | Stanford CEPA |
| 405 | PSLC DataShop KDD Cup 2010 | CMU LearnLab |
| 406 | LearnSphere | CMU LearnLab |
| 407 | Open University Learning Analytics Dataset (OULAD) | The Open University |
| 408 | ASSISTments Dataset | Worcester Polytechnic Institute |
| 409 | EdNet | Riiid |
| 410 | Duolingo SLAM Shared Task | Duolingo |
| 411 | NBER Education Research Data | NBER |
| 412 | TALIS | OECD |
| 413 | PIAAC | OECD |
| 416 | EDFacts Data Files | U.S. Department of Education |

**data.gov — Education datasets**
- URL: https://catalog.data.gov/dataset?groups=education2168
- What it is: Federal open data catalog, education category. Includes state assessment data, CRDC, etc.
- Content types: `dataset`
- Access: Open, machine-readable (JSON/CSV).
- Scale: Selective — curate only datasets directly relevant to LE research.

**CommonLit / Learning Curve datasets (if public)**
- Research datasets from adaptive reading platforms. Check for public releases.

---

### Frameworks & design guides

**CAST — Universal Design for Learning (UDL) Guidelines**
- URL: https://udlguidelines.cast.org
- What it is: Research-based framework for designing flexible learning environments.
- Content types: `framework`
- Access: Open HTML.

**CASEL — SEL Framework**
- URL: https://casel.org/fundamentals-of-sel/what-is-the-casel-framework/
- What it is: The defining framework for social-emotional learning (SEL), widely adopted by districts, states, and federal policy.
- Content types: `framework`
- Access: ✅ Confirmed — open HTML.
- **Indexed:** 1 entry (entry 144): CASEL SEL Framework (2020 update).
- Scale: 1–2 entries (framework + possibly their program guide or equity guide).

**Learning Engineering design frameworks**
- Koedinger, Booth, et al. LE process model papers (target specific papers, not a site)
- IES Logic Model for education research — framework for program evaluation

**ISTE Standards**
- URL: https://iste.org/standards
- What it is: Standards for students, educators, and education leaders in technology integration.
- Content types: `framework`
- Access: Open HTML (standards text); implementation guides may be member-gated.

---

### Professional development

**Teaching Lab**
- URL: https://teachinglab.org/resources
- What it is: Evidence-based PD for teachers. Strong on research backing.
- Content types: `report`, `framework`
- Access: Not yet attempted.

**Learning Forward**
- URL: https://learningforward.org
- What it is: Standards for professional learning. Widely referenced in PD research.
- Content types: `framework`
- Access: Mix of open and member-gated.

---

### Code & open-source tools

**OpenSimon Toolkit (CMU Simon Initiative)**
- URL: https://github.com/CMUCTAT
- What it is: Open-source ITS tools including CTAT (Cognitive Tutor Authoring Tools).
- Content types: `code`
- Access: GitHub — open.

**py-bkt / BKT implementations**
- What it is: Open-source implementations of Bayesian Knowledge Tracing — foundational LE algorithm.
- Content types: `code`
- Access: GitHub — open. Several implementations (Pardos, Badrinath et al.)

**CMU LearnLab GitHub**
- URL: https://github.com/LearnLab
- What it is: Open-source LE research tools from LearnLab.
- Content types: `code`
- Access: GitHub — open.

---

### Field journals (selective indexing only)

Index landmark or highly-cited papers only — do not attempt systematic indexing.

| Journal | Access | URL pattern | Confirmed? | Best use |
|---|---|---|---|---|
| Journal of Educational Data Mining (JEDM) | Fully open access | jedm.educationaldatamining.org/index.php/JEDM/article/view/[ID] | ✅ | **39 indexed**. Vols 10–18 (2018–2026). BKT, hint-seeking, dropout, fairness, LLMs, affect, A/B testing. |
| Journal of Learning Analytics (JLA) | Fully open access, CC BY 4.0 | learning-analytics.info/index.php/JLA/article/view/[ID] | ✅ | **44 indexed**. Vols 9–12 (2022–2025). LA dashboards, temporal modeling, NLP, fairness, writing analytics, collaborative learning. |
| npj Science of Learning | Fully open access (Nature) | nature.com/npjscilearn/articles | ⚠️ 303 redirect — verify URL | High-quality cognitive/neuro/learning science |
| Computers & Education | Paywalled | — | — | Use DOI + Unpaywall/Semantic Scholar |
| Educational Technology Research & Development | Paywalled | — | — | Same |
| AIED conference proceedings | Springer paywall | — | — | dblp.org metadata; Semantic Scholar abstracts |
| EDM proceedings (educationaldatamining.org) | Open access | — | ⚠️ JS-rendered listing | Manual navigation needed |
| Educational Researcher (AERA) | Partially OA | — | — | Landmark review papers only |
| Review of Educational Research (AERA) | Partially OA | — | — | Meta-analyses; use DOI + Unpaywall |

---

## API layer — discovery and abstract fallback

APIs serve two roles in this hub: (1) **discovery** — finding high-quality pre-curated content by funder or quality signal; (2) **abstract fallback** — retrieving descriptions for paywalled entries we can't directly fetch.

### Confirmed working APIs

**OpenAlex** (api.openalex.org)
- Free: 10 req/sec unauthenticated; free account key at openalex.org/settings/api for 100 req/sec
- Abstract fallback: `api.openalex.org/works?filter=doi:10.xxxx/xxxxx&select=title,abstract_inverted_index,open_access`
- Discovery by funder: `api.openalex.org/works?filter=grants.funder:F4320332210,open_access.is_oa:true` — filter by IES (F4320332210) or NSF (F4320306076)
- Note: `abstract_inverted_index` is a word-position dict, not plain text — must be reassembled
- Status: Confirmed working (basic queries). Funder filter syntax needs verification.

**Semantic Scholar** (api.semanticscholar.org/graph/v1)
- Free tier: 1000 req/sec shared across all unauthenticated users — hits rate limits quickly in practice (429)
- Free API key: Register at semanticscholar.org/product/api (email registration, key returned by email)
- With key: 1 req/sec dedicated
- Best use: Finding highly-cited education papers and retrieving open-access PDFs
- Query: `api.semanticscholar.org/graph/v1/paper/search?query=...&fields=title,year,citationCount,openAccessPdf`
- Also: `api.semanticscholar.org/graph/v1/paper/DOI:10.xxxx/xxxxx?fields=abstract,openAccessPdf`
- Status: Confirmed working (basic queries). **API key needed for production use.**

**ERIC** (eric.ed.gov)
- robots.txt: `Disallow:` blank — everything permitted for crawlers
- Individual record pages: `eric.ed.gov/?id=EJ[ID]` — confirmed accessible ✅. Returns full metadata: title, author, journal, year, abstract, peer-reviewed flag, sponsor/funder, subject descriptors.
- Search page: `eric.ed.gov/?q=[query]&ft=on` — HTML-parseable (not JS-rendered) ✅. Returns 15 results per page; supports filters for peer-reviewed, full-text available.
- REST API: `api.eric.ed.gov` hostname does NOT resolve (ECONNREFUSED). No working REST API endpoint confirmed as of this audit.
- Bulk XML downloads: Available by decade at `eric.ed.gov/?download`. ERIC explicitly states these are "available for use by the general public." File sizes unknown; copyright policy governs acceptable use. Metadata and abstracts = public domain/open; full-text PDFs = subject to original publisher rights.
- **How to use for this hub:** Query the search page with quality filters (`ft=on` for full-text, `sponsor:"Institute of Education Sciences"` by subject), follow `?id=EJ[ID]` links, extract metadata from the record page. No API key needed. Respect the robots.txt spirit: targeted queries, not automated mass scraping.
- Key quality filters available: peer-reviewed only, IES-sponsored, full-text on ERIC, subject descriptors (ERIC thesaurus controlled vocabulary).

**Unpaywall** (api.unpaywall.org/v2)
- Free: Use email address as key (no registration, just include `?email=your@email.com`)
- Given a journal DOI → returns legal free version URL (OA repository, author's site, etc.)
- Usage: `api.unpaywall.org/v2/10.xxxx/xxxxx?email=your@email.com`
- **Best use: route around RAND, MDRC, Brookings HTML blocks** — their papers often have OA versions in institutional repositories even when the publisher site is inaccessible. Find the DOI via OpenAlex/Semantic Scholar, then Unpaywall for the free PDF URL.
- Note: Does not work for non-journal content (gray reports, datasets, software). Only covers DOI-registered academic papers.
- Status: Endpoint confirmed (api.unpaywall.org/v2). Test on a Zenodo DOI returned 404 (expected — Zenodo is already OA, Unpaywall focuses on paywalled journal papers).

**CrossRef** (api.crossref.org)
- Free, no key needed
- DOI → full metadata (title, authors, year, journal, funder)
- Usage: `api.crossref.org/works/10.xxxx/xxxxx`
- Status: Confirmed working (standard REST API, no auth).

---

### Robots.txt and crawl status for key sources

| Source | robots.txt finding | Implication |
|---|---|---|
| **ies.ed.gov (WWC, REL)** | Standard Drupal template — crawling allowed | ✅ Full access |
| **Brookings** | Crawling allowed; sitemap at brookings.edu/sitemap_index.xml | ✅ Articles accessible — use sitemap to enumerate URLs |
| **MDRC** | Standard Drupal template — crawling allowed | ⚠️ WAF (Cloudflare-style) blocks automated requests despite allowed robots.txt. May work with browser User-Agent header in production pipeline. |
| **Child Trends** | Explicitly disallows: ClaudeBot, anthropic-ai, Claude-Web (full `Disallow: /`) | ❌ Hard block targeting Anthropic specifically. Dead end. |
| **RAND** | robots.txt itself returns 403 | ❌ Hard block. Use Unpaywall to find OA versions of RAND reports by DOI. |
| **IES/WWC** | Crawling allowed | ✅ But Interventions listing page is JS-rendered — individual intervention pages accessible by slug |

---

### Quality signal: funder IDs for OpenAlex

| Funder | OpenAlex ID | Works count |
|---|---|---|
| Institute of Education Sciences (IES) | F4320332210 | 7,504 |
| National Science Foundation (NSF) | F4320306076 | (not confirmed) |
| Gates Foundation | (not confirmed — query: api.openalex.org/funders?search=gates+foundation) | — |
| Spencer Foundation | (not confirmed) | — |

Use: `api.openalex.org/works?filter=grants.funder:F4320332210,open_access.is_oa:true&sort=cited_by_count:desc` to find highly-cited, open-access, IES-funded education research.

---

### Workaround for blocked sources

For RAND, MDRC, AIR, Brookings (when HTML is inaccessible):
1. Find the paper by title/author in Semantic Scholar or OpenAlex → get DOI
2. Query Unpaywall with DOI → get free PDF URL
3. Fetch the PDF URL (PDFs are often on different hosts not subject to the same WAF)
4. Write entry from PDF content

This allows indexing RAND and MDRC research without ever hitting their blocked HTML pages.

---

## Scale considerations

Pure links + text scales trivially. 10,000 entries ≈ 5MB of text. Not a constraint.

The real question is selectivity. Pre-curated sourcing naturally limits scale — we're bounded by what trusted organizations have surfaced, not by what's indexed in a database of 271M papers. Estimate: 300–800 entries is a realistic well-curated hub covering this field meaningfully.

---

*See `sources-log.md` for access status of previously attempted sources.*  
*See `schema.md` for the no-inference policy on descriptions.*
