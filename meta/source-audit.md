# Source Audit

> Comprehensive accessibility review of every source in the inventory.
> Original audit: 2026-05-01. Refreshed: 2026-05-13 with cloud-routine findings.
> For each source: what's accessible, what's not, API key requirements, format, and recommended approach.
>
> **For the weekly automation routine, START with the "Routine source access matrix" below** —
> it's a fast lookup of the 14 sources the routine touches, with the latest known access method.

---

## Routine source access matrix (refreshed 2026-05-13)

The weekly automation prompt at `meta/automation-prompt.md` walks these 14 sources. This matrix is the agent's lookup: before fetching, check the source's row here; use the recommended method. If WebFetch fails on a source marked "WebFetch ok," try Playwright once before logging as a failure.

| Source | Discovery URL | WebFetch (local) | WebFetch (cloud) | Playwright needed? | Notes |
|---|---|---|---|---|---|
| Evidence for ESSA | sitemap.xml | ✅ | ✅ | No | Sitemap is non-chronological — early-stop heuristic less effective. ~300+ program entries; ~5 secondary sitemaps (program-sitemap2.xml etc.) hold older entries. Drop programs whose page reads "No studies met inclusion requirements" (no usable content per no-inference policy). |
| JEDM | issue/archive | ✅ | ✅ | No | OJS journal. Walk Vol N → article view pages. Reliable. |
| JLA | issue/archive | ✅ | ❌ **403** | **Try Playwright** | Cloud session got 403 on issue and article view pages (2026-05-13). Local Claude Code WebFetch works. Suspected: Anthropic WebFetch proxy IP blocked by OJS host. Playwright with real Chromium headers is the likely fix. |
| Campbell Collaboration | education/reviews/ | ✅ | ❌ **JS-rendered** | **Yes** | Listing page is JS-rendered. WebFetch returns blank. Use Playwright to render the listing, then individual review pages are usually static HTML and WebFetch works. |
| LPI | research/ | ✅ | ✅ | No | Listing reliable. Product pages reliable. |
| EdTrust | research/ | ✅ | ✅ | No | URL pattern: `edtrust.org/resource/[slug]` (note: legacy `/rti/` mentioned below; current is `/resource/`). |
| Brookings (Brown Center only) | sitemap_index.xml | ✅ | ✅ | No | Sitemap is paginated (~55 sub-sitemaps). Filter Brown Center articles only. Skip Brookings Now / news / opinion. |
| WWC Intervention Reports | Search/Products?productType=2 | ✅ | ❌ **403** | **Try Playwright** | Cloud session got 403 on the search/products listing (2026-05-13). Local WebFetch works. Individual `/InterventionReport/[id]` pages: try Playwright; .gov bot detection is the suspected cause. |
| WestEd | resources/?type=research-evaluation | ✅ | ✅ | No | Reliable. Listing returns recent resources. |
| TNTP | publications/ | ⚠️ partial | ⚠️ partial | Yes for full coverage | Listing is JS-paginated (4 pages, 36 total). WebFetch sees page 1 only (10 items). For routine: index what's reachable from page 1, note remainder. For backlog: use `scripts/playwright_scrape.py tntp`. |
| NWEA Research | **publication-sitemap.xml** | ✅ | ✅ | No | Use the sitemap, not the JS-rendered `/research/` listing. Sitemap is exhaustive but **not strictly chronological** — early-stop is less effective; expect to find older publications. |
| Mathematica | evidence?focusArea=Education | ⚠️ partial | ⚠️ partial | Yes for full coverage | Listing is JS-rendered; WebFetch sees a partial set (~8 items). The full set (~693 education pubs) lives behind the Coveo search API at `mathematica.org/coveo/rest/search/v2` with filter `@mprhumanservicetopicsv2==Education`, but it needs a bearer token intercepted via Playwright — fragile. For the routine: index what's reachable from the listing; for backlog: Playwright + Coveo intercept. |
| UChicago Consortium | publications | ✅ | ✅ | No | Reliable. Listing is paginated; recent publications on page 1. |
| CREDO at Stanford | research-reports/report-finder/ | ✅ | ✅ | No | Reliable. |
| IES REL (10 regions) | per-region pages | ✅ | ❌ **403** | **Try Playwright** | Cloud session got 403 on all regional `Products/Region/[region]/Publication/[id]` pages (2026-05-13). Local WebFetch works. .gov bot detection suspected. Probe approach (try recent IDs) only works if WebFetch can reach the pages. |

### Sources explicitly skipped in the routine

Documented here so the agent doesn't try them and waste tokens:

- **Digital Promise** — requires Playwright + DSpace REST API. Use `scripts/playwright_scrape.py digital-promise` manually.
- **RAND Education** — 403 via WebFetch (confirmed 2026-05-01). Manual only.
- **MDRC** — WAF blocks all requests. Manual only.
- **AIMS Collaboratory** — slow publication cadence; check manually a few times a year.

### Playwright fallback pattern (when WebFetch returns 403 or empty)

When the matrix above marks "Try Playwright" or WebFetch returns 403/empty for a source the matrix says should work, follow the installation and runtime pattern in **`meta/playwright-guide.md`**. Cap at one Playwright retry per URL — don't loop. If Playwright also fails, log as a non-critical failure and move on.

### Findings recorded after each run

Any new access surprises (newly-broken URLs, newly-working workarounds, source structure changes) should be appended to `meta/sources-log.md` with the date, so future runs benefit. The automation prompt's Step 9 covers this.

---

## Summary table

| Source | Accessible | API | Key needed | Format | Recommended use |
|---|---|---|---|---|---|
| WWC Practice Guides | ✅ | No | No | HTML + PDF | Selective manual indexing |
| UNESCO AI in Education | ✅ | No | No | HTML + PDF (UNESDOC) | Index ~5 key documents |
| CAST UDL Guidelines | ✅ | No | No | HTML + PDF | 1 entry (framework) |
| JEDM | ✅ | No | No | HTML + PDF (OJS) | Curate landmark papers |
| Digital Promise reports | ✅ | No | No | DSpace (HTML+PDF) | Curate relevant reports |
| ISTE+ASCD | ✅ (partial) | No | No | HTML + PDF (open items) | Open items only |
| Carnegie Learning | ✅ | No | No | HTML + linked PDFs | Curate research reports |
| Duolingo Research | ✅ (partial) | No | No | HTML + PDF (mixed) | 5–10 open papers |
| Teaching Lab | ✅ (limited) | No | No | HTML case studies | Low priority — limited research |
| OpenAlex | ✅ | REST | No (free key for higher limits) | JSON | Abstract fallback only |
| ERIC | ✅ | REST | No | JSON | Abstract fallback / descriptor lookup |
| Khan Academy research | ⚠️ redirects | No | No | — | Dead end — see notes |
| CCSSO | ⚠️ 404s | No | No | — | Try different URL approach |
| Learning Policy Institute | ⚠️ limited fit | No | No | HTML | Low priority — not LE-focused |
| EDM Proceedings | ⚠️ page not found | No | No | HTML + PDF | Try direct year URLs |
| Learning Forward | ⚠️ 404s | No | No | — | Mostly member-gated |

---

## Detailed findings

---

### What Works Clearinghouse (WWC)
**URL:** https://ies.ed.gov/ncee/wwc/  
**Status:** ✅ Accessible  
**API:** None  
**Key required:** No  
**Format:** HTML pages + PDF downloads  

**What's available:**
- Practice Guides: evidence-based recommendations for educators. Browse page: `/ncee/wwc/AllPracticeGuides`
- Intervention Reports: program evaluation summaries. Browse page: `/ncee/wwc/AllInterventionReports`
- Topic areas relevant to us: STEM, Literacy, Early Childhood, English Learners, Social-Emotional Learning, Teachers & Leaders

**How to index:** Visit AllPracticeGuides, identify directly LE-relevant titles (math, early childhood, formative assessment, ELL literacy), fetch each, write entry. Estimated: 10–20 entries.

**Limitations:** Browse pages returned structural HTML but not full title lists via WebFetch — needs either browser navigation or a targeted scrape of the listing pages.

---

### UNESCO — AI in Education
**URL:** https://www.unesco.org/en/digital-education/artificial-intelligence  
**Document host:** https://unesdoc.unesco.org/  
**Status:** ✅ Accessible  
**API:** No  
**Key required:** No  
**Format:** HTML + PDF (UNESDOC open repository)  

**Documents confirmed available:**
| Title | Type | URL |
|---|---|---|
| Artificial intelligence and education: Guidance for policy-makers | Policy framework | unesdoc.unesco.org/ark:/48223/pf0000376709 |
| AI competency frameworks for students and teachers | Framework | (via UNESCO article page) |
| Generative AI and the future of education | Report | unesdoc.unesco.org/ark:/48223/pf0000385877 |
| AI and education: Protecting the rights of learners | Publication | 2025 |
| AI and the future of education: Disruptions, dilemmas and directions | Publication | Sept 2025 |

**How to index:** Fetch each UNESDOC URL directly; all appear freely accessible. Estimated: 4–6 entries.

---

### CAST — Universal Design for Learning (UDL) Guidelines
**URL:** https://udlguidelines.cast.org  
**Status:** ✅ Fully accessible  
**API:** No  
**Key required:** No  
**Format:** Interactive HTML + downloadable PDF graphic organizer  

**What's available:**
- UDL Guidelines 3.0 (current) — 3 principles (Engagement, Representation, Action & Expression), interactive web tool
- PDF versions (downloadable, 20+ language translations)
- Past version: Guidelines 2.2
- Free webinar series, online courses, research evidence pages

**How to index:** 1–2 entries (the Guidelines themselves as a `framework` type; possibly the research evidence page as a separate entry).

---

### Journal of Educational Data Mining (JEDM)
**URL:** https://jedm.educationaldatamining.org/  
**Status:** ✅ Fully accessible  
**API:** None (OJS journal system)  
**Key required:** No  
**Format:** HTML + PDF per article  
**Open access:** Yes — "completely and permanently free and open-access"  

**What's available:**
- Vol 1, No 1 (2009) through Vol 18, No 1 (2026)
- ~400–500 papers total across 17+ years
- HTML and PDF formats per article

**How to index:** Curate only. Don't index wholesale. Target: foundational papers (early volumes establishing EDM methods) + recent high-impact papers. Estimated: 10–15 entries.

**Limitation:** No structured data export or API — requires browsing volume/issue pages.

---

### Digital Promise
**URL:** https://digitalpromise.org/our-reports/  
**Repository:** https://digitalpromise.dspacedirect.org  
**Status:** ✅ Accessible  
**API:** No (DSpace repository — structured but not API)  
**Key required:** No  
**Format:** HTML + PDF (DSpace)  

**Reports confirmed open access:**
- Outcomes of Increased Practitioner Engagement in Edtech Development
- Computational Thinking for an Inclusive World
- Shifting Mindsets: Designing Lessons for Learner Variability
- Breaking With the Past: Embracing Digital Transformation in Education
- The IEP Project: A Strength-based, Whole Learner Teacher Guide
- Research Map: 110,000+ articles indexed (Web of Science 2009–2018 — **not updated**)

**How to index:** Browse /our-reports/, curate LE-relevant reports. The Research Map itself is worth an entry as a resource pointer. Estimated: 4–6 entries.

**Note:** Research Map is based on 2009–2018 Web of Science data — useful as a discovery resource to point practitioners toward, not for extracting entries.

---

### ISTE + ASCD (merged organization)
**URL:** https://iste-ascd.org/ai  
**Status:** ✅ Partial — open items accessible, member/purchase items not  
**API:** No  
**Key required:** No for open items  
**Format:** HTML + PDF (open items); purchase flow (books/courses)  

**Open access confirmed:**
- "AI Lessons" — downloadable guides (English, Spanish, Arabic) — unplugged to chatbots
- "Bringing AI to School" — free PDF guide for education leaders (+ UK version)
- Blog posts on AI implementation
- ISTE Standards (web-accessible)
- EL Magazine articles (some open)

**Member/purchase only (skip):**
- Books: "How to Teach AI", "AI for School Leaders", etc.
- Online courses: "AI Deep Dive for Educators"

**How to index:** Index open PDFs and standards pages only. Estimated: 3–5 entries.

---

### Carnegie Learning Research
**URL:** https://www.carnegielearning.com/research/  
**Status:** ✅ Accessible  
**API:** No  
**Key required:** No  
**Format:** HTML + linked PDFs / external research platforms  

**What's available:**
- ESSA Evidence-Based Approach to Math (PDF)
- ESSA Evidence-Based Approach to Literacy (links to Evidence for ESSA)
- RAND Corporation study on blended math approach
- EMERALDS study results (via Student Achievement Partners)
- EDReports evaluations (external)
- Products covered: MATHia (6-12 math ITS), Elementary Math Solution (K-5), Lenses on Literature (ELA)

**How to index:** Fetch the research page and linked reports. Some link to external evidence platforms (Evidence for ESSA, Achieve the Core) — follow those. Estimated: 3–5 entries.

---

### Duolingo Research
**URL:** https://research.duolingo.com/  
**Status:** ✅ Accessible (partial — mixed access)  
**API:** No  
**Key required:** No  
**Format:** HTML listing + PDF/external links  

**What's available:**
- 18 papers listed (2015–2021)
- Topics: spaced repetition algorithms, language learning assessment, ML in education, notification optimization, test-taking behavior, cognitive science of reading
- Some papers hosted on research.duolingo.com as direct PDFs (open)
- Others link to ACL, EMNLP, KDD proceedings (may require institutional access)

**How to index:** Curate the open-access papers (those hosted on Duolingo's domain). Skip externally-hosted paywalled ones unless we can get abstracts. Estimated: 5–8 entries.

**Relevance note:** Strong on spacing/retrieval practice algorithms — directly relevant to LE methods.

---

### Teaching Lab
**URL:** https://teachinglab.org/impact  
**Status:** ✅ Accessible but limited research content  
**API:** No  
**Key required:** No  
**Format:** HTML case studies  

**What's available:**
- Case studies (Delaware writing pathway, Chicago CPS curriculum implementation)
- Knowledge Hub (teachinglab.org/knowledge-hub/)
- Products: Teaching Lab Studio, Writing Pathway, Podsie (spaced practice app), Multilingual Learner Action Guide
- AI + Education Newsletter

**How to index:** Low priority as a research source. Podsie (spaced practice) is worth an entry as a `platform`. Estimated: 1–2 entries.

---

### OpenAlex API
**URL:** https://api.openalex.org/  
**Status:** ✅ Working  
**API:** REST — confirmed functional  
**Key required:** No for basic queries (free API key for higher rate limits)  
**Format:** JSON  
**Role in this hub:** Abstract fallback only — not a primary source  

**Confirmed fields per result:**
```json
{
  "title": "...",
  "doi": "10.xxxx/...",
  "publication_year": 2024,
  "open_access": {
    "is_oa": true/false,
    "oa_status": "gold/green/closed/...",
    "oa_url": "https://... or null",
    "any_repository_has_fulltext": true/false
  },
  "primary_location": {
    "landing_page_url": "https://..."
  }
}
```

**How to use:** When a pre-curated entry has no accessible abstract, query: `api.openalex.org/works?filter=doi:10.xxxx/xxxxx&select=title,abstract_inverted_index,open_access`. Note: `abstract_inverted_index` must be reassembled into text (it's a word-position dict, not plain text).

**Rate limits:** 10 req/sec unauthenticated; higher with free key from openalex.org/settings/api.

---

### ERIC
**URL:** https://eric.ed.gov/  
**API docs:** https://eric.ed.gov/?api=  
**Status:** ✅ Site accessible; API docs page not loading via WebFetch  
**API:** REST — confirmed to exist; endpoint not confirmed via live fetch  
**Key required:** No (free)  
**Role in this hub:** Abstract fallback; also useful for confirming education-specific descriptors  

**From documentation (prior knowledge):**
- Base URL: `https://api.eric.ed.gov/` (or `eric.ed.gov/api/`)
- Query by: keyword, descriptor (controlled vocabulary), publication type, date range
- Returns: JSON with title, author, abstract, source, publication date, ERIC ID, URL
- 1.6M records, monthly updates, 350,000+ full text

**How to use:** Query by DOI or ERIC ID when a pre-curated entry needs metadata. Also useful for checking what ERIC descriptor terms map to our tags.

---

### Khan Academy Research
**URL:** research.khanacademy.org → redirects to early.khanacademy.org  
**Status:** ⚠️ Dead end  
**Notes:** research.khanacademy.org now redirects to early.khanacademy.org, which hosts only 3 older early-product design studies (2015–2018). This is not Khan Academy's current research output. KA's recent research on Khanmigo and personalized learning is published through academic venues (not aggregated on their site). Try searching OpenAlex/Semantic Scholar by institution: "Khan Academy" for recent papers.

---

### CCSSO
**URL:** https://ccsso.org  
**Status:** ⚠️ Resource library pages returning 404  
**Notes:** ccsso.org/resource-library and ccsso.org/topics/artificial-intelligence both returned 404. The organization exists and publishes AI guidance for state systems, but their site structure is blocking automated fetch. Requires manual browser navigation. Worth a manual attempt — CCSSO AI guidance is directly relevant to Proposer's policy scope.

---

### Learning Policy Institute
**URL:** https://learningpolicyinstitute.org  
**Status:** ⚠️ Accessible but limited fit  
**Notes:** LPI publishes on accountability, equity, teacher quality, school finance — important education policy but not learning engineering. "Science of Learning and Development" is the closest topic area. Low priority unless the hub's scope expands to broad ed policy. Blog pages 404'd; main site accessible.

---

### EDM Conference Proceedings
**URL:** https://educationaldatamining.org  
**Status:** ⚠️ Proceedings archive page not found via automated fetch  
**Notes:** The main site loads but proceedings are not on the pages fetched. Based on prior knowledge: EDM proceedings are open access, hosted at educationaldatamining.org/proceedings/ (try this URL directly in browser). Annually ~100–150 papers. Worth manual navigation for landmark papers.

---

### Learning Forward
**URL:** https://learningforward.org  
**Status:** ⚠️ Key pages returning 404  
**Notes:** Standards for Professional Learning and publications pages 404'd. The organization primarily serves members. Some open content exists (blog, select reports) but the standards documents appear member-gated. Low priority.

---

## CCSSO — manual follow-up needed

Try these URLs manually:
- https://ccsso.org/ai (AI resources)
- https://ccsso.org/publications (publications listing)
- Direct search on ccsso.org for "artificial intelligence"

---

## Recommended indexing order (original, pre-scope-revision)

Based on accessibility and relevance (narrow LE-methods scope):

1. **UNESCO AI documents** — 4–6 entries, all open, URLs confirmed. Do first.
2. **WWC Practice Guides** — 10–20 entries, open, requires browse-page navigation.
3. **CAST UDL** — 1–2 entries, trivially accessible.
4. **ISTE+ASCD open items** — 3–5 entries, open PDFs confirmed.
5. **JEDM landmark papers** — 10–15 entries, fully open, curate carefully.
6. **Carnegie Learning research** — 3–5 entries, mixed access.
7. **Digital Promise reports** — 4–6 entries, all open via DSpace.
8. **Duolingo Research (open papers)** — 5–8 entries.
9. **CCSSO** — pending manual navigation.
10. **EDM proceedings** — pending manual navigation.
11. **Teaching Lab / Podsie** — 1–2 entries, low priority.

---

*Original audit conducted 2026-05-01.*

---

## Re-audit: 2026-05-01 (expanded scope)

**Scope change:** Hub now covers all evidence-based K-12 and higher education — not limited to learning engineering methods. All 30 WWC Practice Guides are in scope. Literacy, SEL, college access, career readiness, and dropout prevention all included.

**Audit method change:** Test confirmed by fetching an actual source document, not just the listing/summary page. A source that only has a listing page accessible (but not individual documents) is marked ⚠️, not ✅.

---

### New sources tested

| Source | Document fetch result | API | Key needed | Format | Status |
|---|---|---|---|---|---|
| CASEL | ✅ Framework page fully readable | No | No | HTML | Index 2–3 entries |
| Learning Policy Institute | ✅ Product pages readable, PDFs freely downloadable | No | No | HTML + PDF | Index 5–10 entries |
| National Academies Press | ✅ Free online read + PDF download (no login required) | No | No | HTML + PDF | Index selectively — landmark reports only |
| Education Trust (EdTrust) | ✅ `/rti/[slug]` reports load, PDFs freely downloadable | No | No | HTML + PDF | Index selectively |
| IES REL | ✅ Main hub loads; free resources confirmed | No | No | HTML + PDF | Navigate product pages; index 5–10 entries |
| Best Evidence Encyclopedia | ✅ Site loads; program reviews accessible | No | No | HTML | Index selectively |
| MDRC | ❌ 403 on all attempted URLs including homepage | No | No | — | Dead end via WebFetch |
| American Institutes for Research (AIR) | ❌ 403 | No | No | — | Dead end via WebFetch |
| Brookings Education | ❌ 403/404 on tested URLs | No | No | — | Dead end via WebFetch |
| RAND Education | ❌ 403 on all attempted report URLs | No | No | — | Dead end via WebFetch |
| Child Trends | ⚠️ Homepage loads; document URLs return 404 | No | No | — | Dead end for now — guessed URLs failed; may work with correct slugs |
| Annenberg Institute at Brown | ❌ ECONNREFUSED | No | No | — | Dead end via WebFetch |
| NCII (Intensive Intervention) | ❌ 403 | No | No | — | Dead end via WebFetch |

---

### CASEL
**URL:** https://casel.org/fundamentals-of-sel/what-is-the-casel-framework/  
**Status:** ✅ Confirmed accessible  
**Test document:** Framework page — full text readable  
**What's available:** The CASEL 5 competencies framework (2020 revision), CASEL program guide (SELect Programs), implementation guides, downloadable resources  
**How to index:** 1 entry for the framework; 1 for the SELect Programs guide if accessible. Estimated: 2 entries.

---

### Learning Policy Institute (LPI)
**URL:** https://learningpolicyinstitute.org/  
**Status:** ✅ Confirmed accessible  
**Test document:** Effective Teacher Professional Development (Darling-Hammond et al., 2017) — product page fully readable, three PDFs (full report, brief, fact sheet) freely downloadable  
**What's available:** Reports on teacher quality, professional development, school design, early childhood, equity. Strong evidence base, freely downloadable PDFs.  
**How to index:** Curate reports directly relevant to instruction, professional development, and equity. Estimated: 5–10 entries.

---

### National Academies Press
**URL:** https://www.nationalacademies.org/  
**Status:** ✅ Confirmed accessible  
**Test document:** How People Learn II (2018) — free online reading + free PDF download; account optional  
**What's available:** Consensus study reports on education, learning science, early childhood, STEM education. Most are freely readable online.  
**Key titles:** How People Learn (2000, foundational), How People Learn II (2018), Transforming the Workforce for Children Birth Through Age 8 (2015), STEM Learning in Afterschool (2015)  
**How to index:** Landmark reports only — likely 3–5 entries total given curation standard.

---

### Education Trust (EdTrust)
**URL:** https://edtrust.org/  
**Status:** ✅ Confirmed accessible  
**Test document:** "The Hidden Bias in College ROI Frameworks" (2026) — page fully readable, PDF freely downloadable  
**What's available:** Research briefs on equity in K-12 and higher education. Strong focus on access, opportunity gaps, and policy. URL pattern: `edtrust.org/rti/[slug]`  
**Relevance note:** EdTrust is an equity-focused advocacy and research org. Their research is high quality and directly relevant to the hub's broader scope. Recommend curating reports on opportunity gaps, teacher diversity, and college access.  
**How to index:** 5–8 entries. Focus on research briefs, not advocacy/press releases.

---

### IES Regional Educational Laboratories (REL)
**URL:** https://ies.ed.gov/ncee/rel/  
**Status:** ✅ Main hub confirmed accessible; product listing pages vary  
**Test document:** REL hub page fully readable; confirmed free toolkits (Mathematics Intervention Toolkit, Teaching Fractions Toolkit) and webinars exist  
**What's available:** 10 regional labs covering all US regions. Products include research reports, toolkits, and applied research studies. All free.  
**Navigation issue:** Product listing pages return 404 for `/Products/Region/[region]` pattern. Need to navigate from the main hub to find specific report URLs.  
**How to index:** Navigate the main hub, identify specific toolkits/reports with accessible URLs. Estimated: 5–10 entries across multiple labs.

---

### Best Evidence Encyclopedia (BEE)
**URL:** https://www.bestevidence.org/  
**Status:** ✅ Homepage loads  
**Test document:** Homepage accessible; program reviews described as openly available; run by Johns Hopkins Center for Research and Reform in Education (same team as Evidence for ESSA)  
**What's available:** Program reviews across reading (elementary, secondary, ELL, struggling readers, technology), mathematics (elementary, secondary, technology), writing, science, early childhood, school reform  
**Navigation issue:** Subdirectory URL patterns have changed from original structure — the old `/reading/beg/beginning_reading.htm` 404s  
**How to index:** Navigate from homepage to subject areas; curate program reviews for well-known programs (Success for All, KIPP, etc.). Estimated: 5–10 entries with careful navigation.

---

## Revised recommended indexing order (expanded scope)

1. **WWC Practice Guides (all 29)** ✅ Complete — entries 1–9, 21–39 indexed.
2. **CASEL** — 2 entries, trivially accessible.
3. **National Academies Press** — 3–5 landmark entries; free online.
4. **Learning Policy Institute** — 5–10 entries; free PDFs.
5. **Education Trust (EdTrust)** — 5–8 entries; free PDFs via `/rti/` pattern.
6. **IES REL** — 5–10 entries; navigate from hub page.
7. **Best Evidence Encyclopedia** — 5–10 entries; navigate from homepage.
8. **JEDM landmark papers** — 10–15 entries, fully open.
9. **UNESCO AI documents** ✅ Complete — entries 11–13 indexed.
10. **CAST UDL** ✅ Complete — entry 10 indexed.
11. **Carnegie Learning research** ✅ Complete — entries 14–16 indexed.
12. **Digital Promise reports** ✅ Complete (with caveats) — entries 18–20 indexed.
13. **ISTE+ASCD open items** — 3–5 entries; open PDFs.
14. **CCSSO** — pending manual navigation.
15. **EDM proceedings** — pending manual navigation.

---

*Re-audit conducted 2026-05-01 under expanded scope.*
