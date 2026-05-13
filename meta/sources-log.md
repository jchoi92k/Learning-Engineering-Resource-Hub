# Sources Log

Tracks every source attempted for the Learning Engineering Resource Hub. Use this to make decisions about future expansion, prioritize re-attempts, and understand what access methods work.

| Source | URL(s) tried | Access | Content type | Value | Notes | Entries added | Date |
|---|---|---|---|---|---|---|---|
| AIMS Collaboratory | aimscollaboratory.org/resources | Yes (scraped) | Resource directory | High | Full scrape 2026-04-27; 74 resources captured | 1–74 | 2026-04-27 |
| The Learning Agency — "A Game-Changer" article | the-learning-agency.com/insights/a-game-changer-lets-talk-about-learning-engineering/ | Yes | Blog post / overview article | High | Accessible; full content readable; good intro to LE field | 75 | 2026-05-01 |
| The Learning Agency — LE Guide | the-learning-agency.com/guides-resources/learning-engineering | Yes | Resource hub page | High | Accessible; lists tools and researchers; TLA's LE landing page | 76 | 2026-05-01 |
| LearnLab (CMU) | learnlab.org | Yes | Research network site | High | Full content accessible; METALS program, research wiki, certificate courses | 77 | 2026-05-01 |
| CMU Simon Initiative | cmu.edu/simon/ | Yes | Initiative hub | High | Accessible; OLI Torus, OpenSimon, DS4EDU, AI Makerspace listed | 78 | 2026-05-01 |
| learningengineering.org | learningengineering.org | Yes (placeholder) | Coming-soon page | Low (now) | Site exists but is a placeholder as of 2026-05-01; no indexed content; worth rechecking | 79 | 2026-05-01 |
| ASSISTments | assistments.org | Yes | Platform site | High | Accessible; E-TRIALS initiative, 200k+ problems, curriculum partnerships listed | 80 | 2026-05-01 |
| PSLC DataShop / LearnSphere | pslcdatashop.web.cmu.edu | Yes | Data repository | High | Accessible; named datasets include ASSISTments Math 2004-07, Physics (Andes), Chinese Vocab, French. LearnSphere workflows listed | 81 | 2026-05-01 |
| CoSN — TeachAI Toolkit | teachai.org/toolkit (via cosn.org/ai) | Yes | Framework/toolkit | High | Accessible via direct URL from CoSN page | 82 | 2026-05-01 |
| CoSN — Operational AI 2025 report | cosn.org/wp-content/uploads/2025/09/2025-HPE-Report_F2.pdf | Yes | PDF report | Medium | Direct PDF URL accessible from cosn.org/ai; couldn't extract full text but URL confirmed | 83 | 2026-05-01 |
| CoSN — K-12 GenAI Maturity Tool | cosn.org/wp-content/uploads/2026/03/K-12-Gen-AI-Maturity-Tool-Final-CC-V1.3.pdf | Yes | PDF framework | Medium | Direct PDF URL confirmed from cosn.org/ai | 84 | 2026-05-01 |
| The 74 — Heffernan article | the74million.org/article/heffernan-how-can-we-know-if-ed-tech-works-... | No (403) | News article | Medium | Blocked; likely requires login or is behind a soft paywall. Could try archive.org or direct author citation | — | 2026-05-01 |
| IES Learning Engineering page | ies.ed.gov/learn/learning-engineering | No (404) | Government page | High (if accessible) | URL not found; IES has reorganized site. Try ies.ed.gov and navigate manually, or search for ICICLE grant program | — | 2026-05-01 |
| IES blog post on LE | ies.ed.gov/blogs/research/post/its-time-to-talk-about-learning-engineering | No (404) | Blog post | High (if accessible) | Same IES site restructure issue. Original post from ~2020; try Wayback Machine | — | 2026-05-01 |
| CMU Simon — LE subpage | cmu.edu/simon/what-we-do/learning-engineering.html | No (404) | Subpage | Medium | Page moved; captured Simon Initiative main page instead (entry 78) | — | 2026-05-01 |
| US Dept of Ed AI guidance | tech.ed.gov/ai/ → ed.gov/ai/ | No (301→404) | Government page | High (if accessible) | Redirect chain ends in 404; site may have moved. Try ed.gov directly and navigate to AI section | — | 2026-05-01 |
| US Dept of Ed AI report PDF | www2.ed.gov/documents/ai-report/ai-report.pdf | Partial | 71-page PDF | High | URL redirects to ed.gov; PDF binary not extractable by fetch tool. Try downloading directly | — | 2026-05-01 |
| OpenAlex | openalex.org | Partial | Academic index platform | High | Homepage only loaded; API at api.openalex.org is the right endpoint for programmatic access (no auth needed). Best used via Python script, not WebFetch | — | 2026-05-01 |
| CoSN AI page (discovery) | cosn.org/ai | Yes | Resource hub | High | Used as discovery page to find CoSN report and tool URLs; not added as its own entry | — | 2026-05-01 |

---

## Access Method Notes

**What works reliably:**
- Static HTML pages (TLA, CMU, LearnLab, ASSISTments, CoSN)
- Direct PDF URLs discovered from a parent HTML page
- Open data repositories (DataShop)

**What doesn't work via WebFetch:**
- PDF binary content (URLs accessible, content not extractable)
- Pages behind soft paywalls or login walls (The74)
- Government sites that have been reorganized (IES, ed.gov)

**What needs a different approach:**
- OpenAlex: use Python `requests` against `api.openalex.org/works?search=learning+engineering` — returns structured JSON
- IES/ed.gov: navigate manually in a browser, then add entries by hand
- PDF content: download and read locally, then write entry

---

---

## Sources identified but not yet attempted (2026-05-01)

| Source | URL | Access model | Value | Next step |
|---|---|---|---|---|
| OpenAlex API | api.openalex.org | Free REST API (CC0) | High — 271M works, best for paper monitoring | Python script; filter by topic + date |
| ERIC API | eric.ed.gov/?api= | Free API | High — 1.6M ed records, monthly updates | Fetch API docs; filter by descriptor |
| Semantic Scholar | api.semanticscholar.org | Free API (rate-limited) | Medium — 200M papers, strong on CS/AI | Use for AI-heavy entries; overlaps OpenAlex |
| What Works Clearinghouse | ies.ed.gov/ncee/wwc/ | HTML (scrapeable) | High — IES gold-standard reviews | Scrape practice guides relevant to math/early childhood/ELL |
| Journal of Educational Data Mining | jedm.educationaldatamining.org | Fully open access | High — peer-reviewed, on-topic | Attempt fetch; index landmark papers |
| Journal of Learning Analytics | learning-analytics.info/index.php/JLA | Open access | High | Attempt fetch |
| EDM Conference proceedings | educationaldatamining.org | Open access HTML | High | Selective indexing |
| DBLP (AIED/EDM/LAK metadata) | dblp.org | Free, structured HTML | Medium — metadata only, no abstracts | Use for titles/DOIs of key conference papers |
| ISLS Repository | repository.isls.org | Open access (403 on fetch) | Medium — selective LE papers only | Try with browser headers; selective only |
| Khan Academy Research | research.khanacademy.org | Not yet attempted | High | Attempt fetch |
| Carnegie Learning Research | carnegielearning.com/research/ | Not yet attempted | High | Attempt fetch |
| Learning Policy Institute | learningpolicyinstitute.org | Open access reports | Medium | Selective — LE/AI-ed relevant only |

---

## Priority Re-attempts

| Source | Why valuable | Suggested approach |
|---|---|---|
| IES Learning Engineering (ICICLE program) | Federal funder of most LE research; authoritative | Manual browser navigation to ies.ed.gov |
| US Dept of Ed AI report | 71-page policy document; useful for policy section | Download PDF directly |
| IES blog "It's Time to Talk About Learning Engineering" | Foundational framing document | Wayback Machine: web.archive.org |
| The74 Heffernan article | Data sharing argument by a key LE figure | Try archive.org or author's personal site |
| OpenAlex API | Auto-fetch new LE papers weekly | Python script: api.openalex.org |
